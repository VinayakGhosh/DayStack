"""Behavior tests for a Member's ordered Today shortlist."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from test_project_workflows import ProjectWorkflowTests

from db.db import get_db
from lib.auth import get_current_user
from models.user import Users
from routes.today import router as today_router
from task_workspace.sqlalchemy_repository import (
    WorkspaceConflict,
    WorkspaceForbidden,
    WorkspaceTodayLimitReached,
)


class TodayTests(ProjectWorkflowTests):
    def test_today_is_ordered_per_member_and_local_date_with_due_groups(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        today_task = self.workspace.create_task(
            self.member_id, project.project_id, "Send brief", None, due_date="2026-09-17"
        )
        overdue_task = self.workspace.create_task(
            self.member_id, project.project_id, "Review contract", None, due_date="2026-09-16"
        )

        self.workspace.add_today_task(self.member_id, overdue_task["task_id"], date(2026, 9, 17))
        self.workspace.add_today_task(self.member_id, today_task["task_id"], date(2026, 9, 17))
        reordered = self.workspace.reorder_today_tasks(
            self.member_id,
            [today_task["task_id"], overdue_task["task_id"]],
            date(2026, 9, 17),
        )

        self.assertEqual(
            [item["task"]["name"] for item in reordered["selected_tasks"]],
            ["Send brief", "Review contract"],
        )
        self.assertEqual([item["position"] for item in reordered["selected_tasks"]], [0, 1])
        self.assertEqual([task["name"] for task in reordered["due_today"]], ["Send brief"])
        self.assertEqual([task["name"] for task in reordered["overdue"]], ["Review contract"])
        self.assertEqual(
            self.workspace.get_today(self.member_id, date(2026, 9, 18))["selected_tasks"], []
        )

    def test_today_limits_selections_and_rejects_completed_or_another_members_task(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        tasks = [
            self.workspace.create_task(self.member_id, project.project_id, f"Task {position}", None)
            for position in range(4)
        ]
        target_date = date(2026, 9, 17)
        for task in tasks[:3]:
            self.workspace.add_today_task(self.member_id, task["task_id"], target_date)

        with self.assertRaises(WorkspaceTodayLimitReached) as reached:
            self.workspace.add_today_task(self.member_id, tasks[3]["task_id"], target_date)
        self.assertEqual(reached.exception.code, "today_limit_reached")

        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        completion = next(status for status in statuses if status.is_completion)
        self.workspace.move_task_to_status(self.member_id, tasks[0]["task_id"], completion.status_id)
        with self.assertRaises(WorkspaceConflict) as completed:
            self.workspace.add_today_task(self.member_id, tasks[0]["task_id"], target_date)
        self.assertEqual(completed.exception.code, "task_not_active")

        other_member_id = uuid4()
        self.db.add(Users(
            user_id=other_member_id,
            first_name="Ravi",
            last_name="Shah",
            email="ravi@example.com",
            hashed_password="hash",
        ))
        self.db.commit()
        other_project = self.workspace.create_project(other_member_id, "Private", None)
        other_task = self.workspace.create_task(other_member_id, other_project.project_id, "Private task", None)
        with self.assertRaises(WorkspaceForbidden):
            self.workspace.add_today_task(self.member_id, other_task["task_id"], target_date)

    def test_today_requires_reorder_to_include_each_selected_task_once(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        tasks = [
            self.workspace.create_task(self.member_id, project.project_id, f"Task {position}", None)
            for position in range(2)
        ]
        target_date = date(2026, 9, 17)
        for task in tasks:
            self.workspace.add_today_task(self.member_id, task["task_id"], target_date)

        with self.assertRaises(WorkspaceConflict) as invalid:
            self.workspace.reorder_today_tasks(
                self.member_id, [tasks[0]["task_id"], tasks[0]["task_id"]], target_date
            )
        self.assertEqual(invalid.exception.code, "invalid_today_order")


class TodayHttpContractTests(ProjectWorkflowTests):
    def setUp(self) -> None:
        super().setUp()
        app = FastAPI()
        app.include_router(today_router, prefix="/v1/today")
        app.dependency_overrides[get_db] = self._get_test_db
        app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(user_id=self.member_id)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        super().tearDown()

    def _get_test_db(self):
        db = self._session_factory()
        try:
            yield db
        finally:
            db.close()

    def test_today_limit_is_exposed_as_a_stable_problem_dto(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        tasks = [
            self.workspace.create_task(self.member_id, project.project_id, f"Task {position}", None)
            for position in range(4)
        ]
        for task in tasks[:3]:
            response = self.client.post(
                "/v1/today/tasks?local_date=2026-09-17", json={"task_id": str(task["task_id"])}
            )
            self.assertEqual(response.status_code, 200)

        limit = self.client.post(
            "/v1/today/tasks?local_date=2026-09-17", json={"task_id": str(tasks[3]["task_id"])}
        )

        self.assertEqual(limit.status_code, 409)
        self.assertEqual(limit.json()["detail"]["code"], "today_limit_reached")
