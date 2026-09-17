"""Behavior tests for private Task Attachments and storage coordination."""

from datetime import datetime, timedelta, timezone
import unittest
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_project_workflows import ProjectWorkflowTests

from db.db import get_db
from lib.auth import get_current_user
from routes.tasks import router as tasks_router
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import (
    WorkspaceAttachmentTooLarge,
    WorkspaceForbidden,
    WorkspaceUnsupportedAttachmentType,
)
from task_workspace.storage import AttachmentObjectMetadata, AttachmentUploadTicket
from task_workspace.storage import get_attachment_storage


class FakePrivateStorage:
    """A signed-storage test adapter; it never exposes object keys to callers."""

    def __init__(self) -> None:
        self.uploaded_keys: set[str] = set()
        self.uploaded_metadata: dict[str, AttachmentObjectMetadata] = {}
        self.deleted_keys: list[str] = []
        self.fail_deletes = False
        self.last_key: str | None = None

    def create_upload(self, attachment_id, media_type: str, byte_size: int) -> AttachmentUploadTicket:
        key = f"private/{attachment_id}"
        self.last_key = key
        self.uploaded_metadata[key] = AttachmentObjectMetadata(media_type=media_type, byte_size=byte_size)
        return AttachmentUploadTicket(
            object_key=key,
            upload_url=f"https://storage.example.test/upload/{attachment_id}",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )

    def finalize_upload(self, object_key: str) -> AttachmentObjectMetadata:
        if object_key not in self.uploaded_keys:
            raise RuntimeError("object was not uploaded")
        return self.uploaded_metadata[object_key]

    def create_download(self, object_key: str, filename: str, media_type: str) -> str:
        if object_key not in self.uploaded_keys:
            raise RuntimeError("object is missing")
        return f"https://storage.example.test/download/{filename}"

    def delete(self, object_key: str) -> None:
        if self.fail_deletes:
            raise RuntimeError("temporary storage outage")
        self.deleted_keys.append(object_key)
        self.uploaded_keys.discard(object_key)


class AttachmentWorkspaceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.behavior = ProjectWorkflowTests()
        self.behavior.setUp()
        self.member_id = self.behavior.member_id
        self.storage = FakePrivateStorage()
        self.workspace = TaskWorkspace(self.behavior.workspace._repository, self.storage)
        self.project = self.workspace.create_project(self.member_id, "Client launch", None)
        self.task = self.workspace.create_task(
            self.member_id, self.project.project_id, "Prepare brief", None
        )

    def tearDown(self) -> None:
        self.behavior.tearDown()

    def test_member_can_upload_finalize_list_and_download_a_private_attachment(self) -> None:
        initiated = self.workspace.initiate_attachment_upload(
            self.member_id,
            self.task["task_id"],
            "client-brief.pdf",
            "application/pdf",
            512,
        )

        self.assertEqual(initiated["attachment"]["state"], "pending")
        self.assertEqual(initiated["attachment"]["filename"], "client-brief.pdf")
        self.assertIn("storage.example.test/upload", initiated["upload_url"])
        self.assertNotIn("object_key", initiated["attachment"])

        self.storage.uploaded_keys.add(self.storage.last_key or "")
        finalized = self.workspace.finalize_attachment_upload(
            self.member_id, self.task["task_id"], initiated["attachment"]["attachment_id"]
        )
        listed = self.workspace.list_attachments(self.member_id, self.task["task_id"])
        download = self.workspace.authorize_attachment_download(
            self.member_id, self.task["task_id"], finalized["attachment_id"]
        )

        self.assertEqual(finalized["state"], "available")
        self.assertEqual([item["attachment_id"] for item in listed], [finalized["attachment_id"]])
        self.assertIn("storage.example.test/download/client-brief.pdf", download["download_url"])

    def test_attachment_policy_and_ownership_are_enforced_before_storage_is_called(self) -> None:
        with self.assertRaises(WorkspaceUnsupportedAttachmentType) as unsupported:
            self.workspace.initiate_attachment_upload(
                self.member_id, self.task["task_id"], "script.exe", "application/octet-stream", 100
            )
        self.assertEqual(unsupported.exception.code, "attachment_type_not_allowed")
        self.assertIsNone(self.storage.last_key)

        with self.assertRaises(WorkspaceAttachmentTooLarge) as too_large:
            self.workspace.initiate_attachment_upload(
                self.member_id, self.task["task_id"], "large.pdf", "application/pdf", 10 * 1024 * 1024 + 1
            )
        self.assertEqual(too_large.exception.code, "attachment_too_large")

        with self.assertRaises(WorkspaceForbidden):
            self.workspace.initiate_attachment_upload(
                uuid4(), self.task["task_id"], "brief.pdf", "application/pdf", 100
            )
        self.assertIsNone(self.storage.last_key)

    def test_finalization_rejects_an_object_that_exceeds_its_signed_upload_size(self) -> None:
        initiated = self.workspace.initiate_attachment_upload(
            self.member_id, self.task["task_id"], "brief.pdf", "application/pdf", 512
        )
        key = self.storage.last_key or ""
        self.storage.uploaded_keys.add(key)
        self.storage.uploaded_metadata[key] = AttachmentObjectMetadata(
            media_type="application/pdf", byte_size=10 * 1024 * 1024 + 1
        )

        with self.assertRaises(WorkspaceAttachmentTooLarge):
            self.workspace.finalize_attachment_upload(
                self.member_id, self.task["task_id"], initiated["attachment"]["attachment_id"]
            )

        self.assertEqual(self.workspace.list_attachments(self.member_id, self.task["task_id"]), [])

    def test_task_deletion_queues_failed_private_object_cleanup_for_retry(self) -> None:
        initiated = self.workspace.initiate_attachment_upload(
            self.member_id, self.task["task_id"], "brief.pdf", "application/pdf", 100
        )
        self.storage.uploaded_keys.add(self.storage.last_key or "")
        self.workspace.finalize_attachment_upload(
            self.member_id, self.task["task_id"], initiated["attachment"]["attachment_id"]
        )

        self.storage.fail_deletes = True
        self.workspace.delete_task(self.member_id, self.task["task_id"])
        self.assertEqual(self.storage.deleted_keys, [])

        self.storage.fail_deletes = False
        self.assertEqual(self.workspace.retry_attachment_cleanup(), 1)
        self.assertEqual(len(self.storage.deleted_keys), 1)

    def test_another_member_cannot_download_or_delete_an_attachment(self) -> None:
        initiated = self.workspace.initiate_attachment_upload(
            self.member_id, self.task["task_id"], "brief.pdf", "application/pdf", 100
        )
        self.storage.uploaded_keys.add(self.storage.last_key or "")
        attachment = self.workspace.finalize_attachment_upload(
            self.member_id, self.task["task_id"], initiated["attachment"]["attachment_id"]
        )

        with self.assertRaises(WorkspaceForbidden):
            self.workspace.authorize_attachment_download(uuid4(), self.task["task_id"], attachment["attachment_id"])
        with self.assertRaises(WorkspaceForbidden):
            self.workspace.delete_attachment(uuid4(), self.task["task_id"], attachment["attachment_id"])

    def test_member_deleting_an_attachment_removes_metadata_and_retries_cleanup(self) -> None:
        initiated = self.workspace.initiate_attachment_upload(
            self.member_id, self.task["task_id"], "brief.pdf", "application/pdf", 100
        )
        self.storage.uploaded_keys.add(self.storage.last_key or "")
        attachment = self.workspace.finalize_attachment_upload(
            self.member_id, self.task["task_id"], initiated["attachment"]["attachment_id"]
        )

        self.storage.fail_deletes = True
        self.workspace.delete_attachment(self.member_id, self.task["task_id"], attachment["attachment_id"])
        self.assertEqual(self.workspace.list_attachments(self.member_id, self.task["task_id"]), [])

        self.storage.fail_deletes = False
        self.assertEqual(self.workspace.retry_attachment_cleanup(), 1)
        self.assertEqual(len(self.storage.deleted_keys), 1)

    def test_project_deletion_coordinates_private_object_cleanup(self) -> None:
        initiated = self.workspace.initiate_attachment_upload(
            self.member_id, self.task["task_id"], "brief.pdf", "application/pdf", 100
        )
        self.storage.uploaded_keys.add(self.storage.last_key or "")
        self.workspace.finalize_attachment_upload(
            self.member_id, self.task["task_id"], initiated["attachment"]["attachment_id"]
        )

        self.workspace.delete_project(self.member_id, self.project.project_id)

        self.assertEqual(len(self.storage.deleted_keys), 1)


class AttachmentHttpContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.behavior = ProjectWorkflowTests()
        self.behavior.setUp()
        self.storage = FakePrivateStorage()
        self.member_id = self.behavior.member_id
        self.workspace = TaskWorkspace(self.behavior.workspace._repository, self.storage)
        self.project = self.workspace.create_project(self.member_id, "Client launch", None)
        self.task = self.workspace.create_task(
            self.member_id, self.project.project_id, "Prepare brief", None
        )
        app = FastAPI()
        app.include_router(tasks_router, prefix="/v1/tasks")
        app.dependency_overrides[get_db] = self._get_test_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(user_id=self.member_id)
        app.dependency_overrides[get_attachment_storage] = lambda: self.storage
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.behavior.tearDown()

    def _get_test_db(self):
        db = self.behavior._session_factory()
        try:
            yield db
        finally:
            db.close()

    def test_attachment_http_contract_never_returns_storage_keys(self) -> None:
        initiated = self.client.post(
            f"/v1/tasks/{self.task['task_id']}/attachments",
            json={"filename": "client-brief.pdf", "media_type": "application/pdf", "byte_size": 512},
        )
        self.assertEqual(initiated.status_code, 200)
        body = initiated.json()
        self.assertEqual(body["attachment"]["state"], "pending")
        self.assertIn("upload_url", body)
        self.assertNotIn("storage_key", body["attachment"])

        self.storage.uploaded_keys.add(self.storage.last_key or "")
        attachment_id = body["attachment"]["attachment_id"]
        finalized = self.client.post(
            f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}/finalize"
        )
        self.assertEqual(finalized.status_code, 200)
        self.assertEqual(finalized.json()["state"], "available")

        download = self.client.get(
            f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}/download"
        )
        self.assertEqual(download.status_code, 200)
        self.assertEqual(set(download.json()), {"download_url"})

    def test_attachment_http_contract_returns_a_stable_policy_problem(self) -> None:
        response = self.client.post(
            f"/v1/tasks/{self.task['task_id']}/attachments",
            json={"filename": "script.exe", "media_type": "application/octet-stream", "byte_size": 512},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "attachment_type_not_allowed")
