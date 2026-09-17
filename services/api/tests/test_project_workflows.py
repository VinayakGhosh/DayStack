"""Behavior tests for Project quotas and project-scoped Workflow statuses."""

import os
import unittest
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
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
from lib.auth import get_current_user
from models.Project import ProjectStatus, Projects
from models.Task import TaskStatusHistory, Tasks
from models.user import Users
from routes.projects import router as projects_router
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import (
    SqlAlchemyTaskWorkspaceRepository,
    WorkspaceConflict,
    WorkspaceProjectLimitReached,
)


class ProjectWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        event.listen(engine, "connect", lambda connection, _: connection.create_function("now", 0, lambda: "2026-09-17 00:00:00"))
        for table in (Users.__table__, Projects.__table__, ProjectStatus.__table__, Tasks.__table__, TaskStatusHistory.__table__):
            table.create(engine)
        self._session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        self.db = self._session_factory()
        self.member_id = uuid4()
        self.db.add(Users(
            user_id=self.member_id,
            first_name="Asha",
            last_name="Rao",
            email="asha@example.com",
            hashed_password="hash",
        ))
        self.db.commit()
        self.workspace = TaskWorkspace(SqlAlchemyTaskWorkspaceRepository(self.db))

    def tearDown(self) -> None:
        self.db.close()

    def test_new_project_has_default_workflow_and_usage(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)

        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        usage = self.workspace.project_quota(self.member_id)

        self.assertEqual([status.name for status in statuses], ["To Do", "In Progress", "Completed"])
        self.assertEqual([status.display_order for status in statuses], [0, 1, 2])
        self.assertEqual([status.name for status in statuses if status.is_completion], ["Completed"])
        self.assertEqual(usage, {"used": 1, "limit": 5, "remaining": 4})

    def test_member_cannot_create_more_than_five_projects(self) -> None:
        for position in range(5):
            self.workspace.create_project(self.member_id, f"Project {position}", None)

        with self.assertRaises(WorkspaceProjectLimitReached) as raised:
            self.workspace.create_project(self.member_id, "One too many", None)

        self.assertEqual(raised.exception.code, "project_limit_reached")
        self.assertEqual(self.workspace.project_quota(self.member_id)["used"], 5)

    def test_member_can_reorder_choose_completion_and_reassign_before_removing_a_status(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        initial_statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        custom = self.workspace.create_status(self.member_id, project.project_id, "Ready for review", None)

        self.workspace.reorder_statuses(
            self.member_id,
            project.project_id,
            [custom.status_id, *(status.status_id for status in initial_statuses)],
        )
        promoted = self.workspace.update_status(
            self.member_id,
            project.project_id,
            custom.status_id,
            None,
            None,
            is_completion=True,
        )
        task = self.workspace.create_task(self.member_id, project.project_id, "Review the brief", None)
        replacement = initial_statuses[0]
        self.workspace.update_status(
            self.member_id,
            project.project_id,
            replacement.status_id,
            None,
            None,
            is_completion=True,
        )

        with self.assertRaises(WorkspaceConflict) as raised:
            self.workspace.delete_status(self.member_id, project.project_id, custom.status_id)

        self.assertEqual(raised.exception.code, "status_in_use")
        self.workspace.delete_status(
            self.member_id,
            project.project_id,
            custom.status_id,
            reassign_to_status_id=replacement.status_id,
        )
        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        moved_task = self.workspace.list_tasks(self.member_id, task["task_id"], None, None)[0]

        self.assertEqual([status.display_order for status in statuses], list(range(len(statuses))))
        self.assertEqual([status.status_id for status in statuses if status.is_completion], [replacement.status_id])
        self.assertEqual(moved_task["status_id"], replacement.status_id)


class ProjectWorkflowHttpContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.behavior = ProjectWorkflowTests()
        self.behavior.setUp()
        self.member_id = self.behavior.member_id
        app = FastAPI()
        app.include_router(projects_router, prefix="/v1/project")
        app.dependency_overrides[get_db] = self._get_test_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(user_id=self.member_id)
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

    def test_project_limit_has_a_stable_problem_code(self) -> None:
        for position in range(5):
            response = self.client.post("/v1/project/", json={"name": f"Project {position}"})
            self.assertEqual(response.status_code, 200)

        limit = self.client.post("/v1/project/", json={"name": "One too many"})

        self.assertEqual(limit.status_code, 409)
        self.assertEqual(limit.json()["detail"]["code"], "project_limit_reached")

    def test_another_members_project_returns_a_stable_forbidden_problem(self) -> None:
        other_member_id = uuid4()
        db = self.behavior._session_factory()
        try:
            db.add(Users(
                user_id=other_member_id,
                first_name="Ravi",
                last_name="Shah",
                email="ravi@example.com",
                hashed_password="hash",
            ))
            project = Projects(owner_user_id=other_member_id, organization_id=None, name="Private work")
            db.add(project)
            db.commit()
            project_id = str(project.project_id)
        finally:
            db.close()

        response = self.client.get(f"/v1/project/{project_id}")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "forbidden")


if __name__ == "__main__":
    unittest.main()
