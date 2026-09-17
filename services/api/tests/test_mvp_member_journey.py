"""End-to-end HTTP contract for the essential DayStack member journey."""

import os
import unittest
from datetime import datetime, timezone
from uuid import UUID

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "15")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "14")
os.environ.setdefault("DATABASE_USER", "test")
os.environ.setdefault("DATABASE_PASSWORD", "test")
os.environ.setdefault("DATABASE_HOST", "localhost")
os.environ.setdefault("DATABASE_PORT", "5432")
os.environ.setdefault("DATABASE_NAME", "test")

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from db.db import get_db
from models.organization import Organization
from models.Project import ProjectStatus, Projects
from models.Task import (
    AttachmentCleanupJobs,
    Attachments,
    Labels,
    Subtasks,
    TaskLabels,
    TaskStatusHistory,
    Tasks,
    TodaySelections,
)
from models.user import MemberSessions, Users
from routes import api_router
from task_workspace.storage import (
    AttachmentObjectMetadata,
    AttachmentUploadTicket,
    get_attachment_storage,
)


class FakePrivateStorage:
    def __init__(self) -> None:
        self.objects: dict[str, AttachmentObjectMetadata] = {}

    def create_upload(self, attachment_id: UUID, media_type: str, byte_size: int) -> AttachmentUploadTicket:
        object_key = f"private/{attachment_id}"
        self.objects[object_key] = AttachmentObjectMetadata(media_type=media_type, byte_size=byte_size)
        return AttachmentUploadTicket(
            object_key=object_key,
            upload_url=f"https://storage.example.test/{attachment_id}",
            expires_at=datetime.now(timezone.utc),
        )

    def finalize_upload(self, object_key: str) -> AttachmentObjectMetadata:
        return self.objects[object_key]

    def create_download(self, object_key: str, filename: str, media_type: str) -> str:
        return f"https://storage.example.test/download/{filename}"

    def delete(self, object_key: str) -> None:
        self.objects.pop(object_key, None)


class MvpMemberJourneyTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        event.listen(engine, "connect", lambda connection, _: connection.create_function("now", 0, lambda: "2026-09-17 00:00:00"))
        for table in (
            Users.__table__, Organization.__table__,
            MemberSessions.__table__, Projects.__table__, ProjectStatus.__table__,
            Tasks.__table__, TaskStatusHistory.__table__, Labels.__table__, TaskLabels.__table__,
            Subtasks.__table__, TodaySelections.__table__, Attachments.__table__, AttachmentCleanupJobs.__table__,
        ):
            table.create(engine)
        self._session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        self.storage = FakePrivateStorage()
        app = FastAPI()
        app.include_router(api_router, prefix="/v1")
        app.dependency_overrides[get_db] = self._get_test_db
        app.dependency_overrides[get_attachment_storage] = lambda: self.storage
        self.client = TestClient(app, base_url="https://testserver")

    def tearDown(self) -> None:
        self.client.close()

    def _get_test_db(self):
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def test_member_can_sign_up_organize_prioritize_complete_and_attach_work(self) -> None:
        member = self.client.post("/v1/sessions/signup", json={
            "display_name": "Asha Rao",
            "email": "asha@example.com",
            "password": "correct-horse-battery-staple",
            "time_zone": "Asia/Kolkata",
        })
        self.assertEqual(member.status_code, 201)

        project = self.client.post("/v1/project/", json={"name": "Launch", "description": "Client work"})
        self.assertEqual(project.status_code, 200)
        project_id = project.json()["project_id"]
        self.assertNotIn("organization_id", project.json())
        self.assertEqual(self.client.get("/v1/project/usage").json(), {"used": 1, "limit": 5, "remaining": 4})

        first_task = self.client.post("/v1/tasks/", json={"project_id": project_id, "name": "Write brief", "priority": "high"})
        second_task = self.client.post("/v1/tasks/", json={"project_id": project_id, "name": "Review brief", "priority": "medium"})
        self.assertEqual(first_task.status_code, 200)
        self.assertEqual(second_task.status_code, 200)
        task_id = first_task.json()["task_id"]

        today = self.client.post("/v1/today/tasks", json={"task_id": task_id})
        self.assertEqual(today.status_code, 200)
        self.assertEqual([item["task"]["name"] for item in today.json()["selected_tasks"]], ["Write brief"])

        statuses = self.client.get(f"/v1/project/{project_id}/statuses").json()
        completion_status = next(status for status in statuses if status["is_completion"])
        completed = self.client.post(
            f"/v1/tasks/{second_task.json()['task_id']}/move",
            json={"status_id": completion_status["status_id"]},
        )
        self.assertEqual(completed.status_code, 200)
        self.assertEqual(self.client.get(f"/v1/tasks/project/{project_id}/usage").json()["used"], 1)

        active_tasks = [first_task.json()["task_id"]]
        for number in range(29):
            created = self.client.post(
                "/v1/tasks/",
                json={"project_id": project_id, "name": f"Capacity task {number}"},
            )
            self.assertEqual(created.status_code, 200)
            active_tasks.append(created.json()["task_id"])
        task_limit = self.client.post("/v1/tasks/", json={"project_id": project_id, "name": "Over capacity"})
        self.assertEqual(task_limit.status_code, 409)
        self.assertEqual(task_limit.json()["detail"]["code"], "task_limit_reached")
        released_task = self.client.post(
            f"/v1/tasks/{active_tasks[-1]}/move",
            json={"status_id": completion_status["status_id"]},
        )
        self.assertEqual(released_task.status_code, 200)
        self.assertEqual(self.client.post("/v1/tasks/", json={"project_id": project_id, "name": "Capacity restored"}).status_code, 200)

        extra_projects = []
        for number in range(4):
            created = self.client.post("/v1/project/", json={"name": f"Project {number}"})
            self.assertEqual(created.status_code, 200)
            extra_projects.append(created.json()["project_id"])
        project_limit = self.client.post("/v1/project/", json={"name": "Over capacity"})
        self.assertEqual(project_limit.status_code, 409)
        self.assertEqual(project_limit.json()["detail"]["code"], "project_limit_reached")
        self.assertEqual(self.client.delete(f"/v1/project/{extra_projects[-1]}").status_code, 204)
        self.assertEqual(self.client.post("/v1/project/", json={"name": "Capacity restored"}).status_code, 200)

        upload = self.client.post(
            f"/v1/tasks/{task_id}/attachments",
            json={"filename": "brief.pdf", "media_type": "application/pdf", "byte_size": 5},
        )
        self.assertEqual(upload.status_code, 200)
        attachment = upload.json()["attachment"]
        self.assertNotIn("storage_key", upload.text)
        finalized = self.client.post(f"/v1/tasks/{task_id}/attachments/{attachment['attachment_id']}/finalize")
        self.assertEqual(finalized.status_code, 200)
        download = self.client.get(f"/v1/tasks/{task_id}/attachments/{attachment['attachment_id']}/download")
        self.assertEqual(download.status_code, 200)
        self.assertIn("storage.example.test/download/brief.pdf", download.json()["download_url"])


if __name__ == "__main__":
    unittest.main()
