"""Authenticated HTTP contracts for database-backed Task Attachments."""

import io
import unittest
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from PIL import Image

from db.db import get_db
from lib.auth import get_current_user
from routes import api_router
from test_project_workflows import ProjectWorkflowTests
from task_workspace.sqlalchemy_repository import WorkspaceForbidden


class AttachmentHttpContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.behavior = ProjectWorkflowTests()
        self.behavior.setUp()
        self.current_member_id = self.behavior.member_id
        self.workspace = self.behavior.workspace
        self.project = self.workspace.create_project(self.current_member_id, "Client launch", None)
        self.task = self.workspace.create_task(
            self.current_member_id, self.project.project_id, "Prepare brief", None
        )
        app = FastAPI()
        app.include_router(api_router, prefix="/v1")
        app.dependency_overrides[get_db] = self._get_test_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(user_id=self.current_member_id)
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

    def _upload(self, filename: str, content: bytes, media_type: str):
        return self.client.post(
            f"/v1/tasks/{self.task['task_id']}/attachments",
            files={"file": (filename, content, media_type)},
        )

    def _finalize(self, attachment_id: str):
        return self.client.post(
            f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}/finalize"
        )

    def test_member_can_upload_finalize_and_download_a_private_attachment(self) -> None:
        uploaded = self._upload("client-brief.pdf", b"confidential brief", "application/pdf")

        self.assertEqual(uploaded.status_code, 200)
        attachment = uploaded.json()
        self.assertEqual(attachment["state"], "pending")
        self.assertNotIn("storage_key", uploaded.text)

        pending_download = self.client.get(
            f"/v1/tasks/{self.task['task_id']}/attachments/{attachment['attachment_id']}/download"
        )
        self.assertEqual(pending_download.status_code, 409)
        self.assertEqual(pending_download.json()["detail"]["code"], "attachment_pending")

        finalized = self._finalize(attachment["attachment_id"])
        self.assertEqual(finalized.status_code, 200)
        self.assertEqual(finalized.json()["state"], "available")

        download = self.client.get(
            f"/v1/tasks/{self.task['task_id']}/attachments/{attachment['attachment_id']}/download"
        )
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.content, b"confidential brief")
        self.assertEqual(download.headers["content-type"], "application/pdf")

    def test_task_workspace_keeps_attachment_content_private_until_finalized(self) -> None:
        attachment = self.workspace.initiate_attachment_upload(
            self.current_member_id,
            self.task["task_id"],
            "client-brief.pdf",
            "application/pdf",
            b"confidential brief",
        )
        with self.assertRaises(WorkspaceForbidden):
            self.workspace.authorize_attachment_download(uuid4(), self.task["task_id"], attachment["attachment_id"])

        finalized = self.workspace.finalize_attachment_upload(
            self.current_member_id, self.task["task_id"], attachment["attachment_id"]
        )
        stored, content = self.workspace.authorize_attachment_download(
            self.current_member_id, self.task["task_id"], finalized["attachment_id"]
        )
        self.assertEqual(stored.media_type, "application/pdf")
        self.assertEqual(content, b"confidential brief")

        self.workspace.delete_attachment(self.current_member_id, self.task["task_id"], finalized["attachment_id"])
        self.assertEqual(self.workspace.list_attachments(self.current_member_id, self.task["task_id"]), [])

    def test_another_member_cannot_download_or_delete_an_attachment(self) -> None:
        uploaded = self._upload("client-brief.pdf", b"confidential brief", "application/pdf")
        attachment_id = uploaded.json()["attachment_id"]
        self.assertEqual(self._finalize(attachment_id).status_code, 200)

        self.current_member_id = uuid4()
        download = self.client.get(f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}/download")
        deletion = self.client.delete(f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}")

        self.assertEqual(download.status_code, 403)
        self.assertEqual(deletion.status_code, 403)

    def test_deleting_a_task_removes_its_attachment(self) -> None:
        uploaded = self._upload("client-brief.pdf", b"confidential brief", "application/pdf")
        attachment_id = uploaded.json()["attachment_id"]
        self.assertEqual(self._finalize(attachment_id).status_code, 200)

        self.assertEqual(self.client.delete(f"/v1/tasks/{self.task['task_id']}").status_code, 204)
        download = self.client.get(f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}/download")

        self.assertEqual(download.status_code, 404)

    def test_deleting_a_project_removes_its_attachment(self) -> None:
        uploaded = self._upload("client-brief.pdf", b"confidential brief", "application/pdf")
        attachment_id = uploaded.json()["attachment_id"]
        self.assertEqual(self._finalize(attachment_id).status_code, 200)

        self.assertEqual(self.client.delete(f"/v1/project/{self.project.project_id}").status_code, 204)
        download = self.client.get(f"/v1/tasks/{self.task['task_id']}/attachments/{attachment_id}/download")

        self.assertEqual(download.status_code, 404)

    def test_static_images_are_normalized_to_webp_below_the_target_size(self) -> None:
        image = Image.new("RGB", (1200, 900), color=(30, 60, 120))
        source = io.BytesIO()
        image.save(source, format="PNG")

        uploaded = self._upload("plan.png", source.getvalue(), "image/png")

        self.assertEqual(uploaded.status_code, 200)
        attachment = uploaded.json()
        self.assertEqual(attachment["filename"], "plan.webp")
        self.assertEqual(attachment["media_type"], "image/webp")
        self.assertLessEqual(attachment["byte_size"], 800 * 1024)

    def test_large_static_image_is_compressed_below_the_target_size(self) -> None:
        image = Image.effect_noise((1800, 1200), 100)
        source = io.BytesIO()
        image.save(source, format="PNG")
        self.assertGreater(len(source.getvalue()), 1024 * 1024)

        uploaded = self._upload("large-plan.png", source.getvalue(), "image/png")

        self.assertEqual(uploaded.status_code, 200)
        self.assertLessEqual(uploaded.json()["byte_size"], 800 * 1024)

    def test_animated_gifs_are_rejected(self) -> None:
        first = Image.new("RGB", (20, 20), color="red")
        second = Image.new("RGB", (20, 20), color="blue")
        source = io.BytesIO()
        first.save(source, format="GIF", save_all=True, append_images=[second], loop=0)

        response = self._upload("animated.gif", source.getvalue(), "image/gif")

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"]["code"], "attachment_type_not_allowed")

    def test_single_frame_gifs_are_normalized_to_webp(self) -> None:
        source = io.BytesIO()
        Image.new("RGB", (20, 20), color="red").save(source, format="GIF")

        response = self._upload("still.gif", source.getvalue(), "image/gif")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "still.webp")
        self.assertEqual(response.json()["media_type"], "image/webp")


if __name__ == "__main__":
    unittest.main()
