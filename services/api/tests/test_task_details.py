"""Behavior tests for MVP Task details, Labels, Subtasks, and active-task quota."""

from test_project_workflows import ProjectWorkflowTests

from models.Task import Attachments, Labels, Tasks, TaskStatusHistory
from task_workspace.sqlalchemy_repository import WorkspaceConflict, WorkspaceTaskLimitReached


class TaskDetailsTests(ProjectWorkflowTests):
    def test_task_response_includes_available_attachment_count(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        task = self.workspace.create_task(self.member_id, project.project_id, "Prepare brief", None)
        self.db.add_all([
            Attachments(task_id=task["task_id"], filename="brief.pdf", media_type="application/pdf", byte_size=12, upload_state="available"),
            Attachments(task_id=task["task_id"], filename="draft.pdf", media_type="application/pdf", byte_size=8, upload_state="pending"),
        ])
        self.db.commit()

        refreshed = self.workspace.list_tasks(self.member_id, task["task_id"], None, None)[0]

        self.assertEqual(refreshed["attachment_count"], 1)

    def test_staged_label_names_are_reused_or_created_with_task_save(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        existing = self.workspace.create_label(self.member_id, "Research", None)

        task = self.workspace.create_task(
            self.member_id,
            project.project_id,
            "Prepare brief",
            None,
            label_ids=[existing["label_id"]],
            label_names=["  Client Work  ", "research"],
        )

        self.assertEqual([label["name"] for label in task["labels"]], ["Client Work", "Research"])
        self.assertEqual(self.db.query(Labels).filter(Labels.member_id == self.member_id).count(), 2)

    def test_failed_task_save_rolls_back_staged_labels(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)

        with self.assertRaises(WorkspaceConflict):
            self.workspace.create_task(
                self.member_id,
                project.project_id,
                "Prepare brief",
                None,
                label_names=["Temporary"],
                subtasks=[{"text": "   ", "is_completed": False}],
            )

        self.assertEqual(self.db.query(Labels).filter(Labels.member_id == self.member_id).count(), 0)

    def test_completion_toggle_reopens_in_most_recent_valid_active_status(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        active = statuses[1]
        completion = next(status for status in statuses if status.is_completion)
        task = self.workspace.create_task(self.member_id, project.project_id, "Prepare brief", None)
        self.workspace.move_task_to_status(self.member_id, task["task_id"], active.status_id)

        completed = self.workspace.set_task_completed(self.member_id, task["task_id"], True)
        reopened = self.workspace.set_task_completed(self.member_id, task["task_id"], False)

        self.assertEqual(completed["status_id"], completion.status_id)
        self.assertEqual(reopened["status_id"], active.status_id)

    def test_reopen_falls_back_to_first_active_status_when_history_is_absent(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        completion = next(status for status in statuses if status.is_completion)
        task = self.workspace.create_task(self.member_id, project.project_id, "Prepare brief", None)
        self.db.query(TaskStatusHistory).filter(TaskStatusHistory.task_id == task["task_id"]).delete()
        stored = self.db.query(Tasks).filter(Tasks.task_id == task["task_id"]).one()
        stored.status_id = completion.status_id
        stored.status_name = completion.name
        self.db.commit()

        reopened = self.workspace.set_task_completed(self.member_id, task["task_id"], False)

        self.assertEqual(reopened["status_id"], statuses[0].status_id)

    def test_reopen_ignores_a_deleted_prior_active_status(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        prior = statuses[1]
        task = self.workspace.create_task(self.member_id, project.project_id, "Prepare brief", None)
        self.workspace.move_task_to_status(self.member_id, task["task_id"], prior.status_id)
        self.workspace.set_task_completed(self.member_id, task["task_id"], True)
        self.workspace.delete_status(self.member_id, project.project_id, prior.status_id)

        reopened = self.workspace.set_task_completed(self.member_id, task["task_id"], False)

        self.assertEqual(reopened["status_id"], statuses[0].status_id)

    def test_task_details_labels_and_subtasks_are_member_scoped_and_ordered(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        task = self.workspace.create_task(
            self.member_id,
            project.project_id,
            "Prepare brief",
            "First draft",
            due_date="2026-09-20",
            priority="high",
        )
        label = self.workspace.create_label(self.member_id, "Client", "#2563eb")

        updated = self.workspace.update_task(
            self.member_id,
            task["task_id"],
            None,
            None,
            due_date="2026-09-21",
            priority="medium",
            label_ids=[label["label_id"]],
            subtasks=[
                {"text": "Outline", "is_completed": True},
                {"text": "Send draft", "is_completed": False},
            ],
        )

        self.assertEqual(str(updated["due_date"]), "2026-09-21")
        self.assertEqual(updated["priority"], "medium")
        self.assertEqual(updated["labels"], [{"label_id": label["label_id"], "name": "Client", "color": "#2563eb"}])
        self.assertEqual(
            [(subtask["text"], subtask["display_order"], subtask["is_completed"]) for subtask in updated["subtasks"]],
            [("Outline", 0, True), ("Send draft", 1, False)],
        )
        cleared = self.workspace.update_task(
            self.member_id, task["task_id"], None, None, due_date=None,
            updated_fields={"description", "due_date"},
        )
        self.assertIsNone(cleared["description"])
        self.assertIsNone(cleared["due_date"])

    def test_thirty_active_tasks_are_enforced_and_completion_releases_capacity(self) -> None:
        project = self.workspace.create_project(self.member_id, "Client launch", None)
        statuses = self.workspace.list_statuses(self.member_id, project.project_id)
        completion = next(status for status in statuses if status.is_completion)

        for position in range(30):
            self.workspace.create_task(self.member_id, project.project_id, f"Task {position}", None)

        with self.assertRaises(WorkspaceTaskLimitReached) as raised:
            self.workspace.create_task(self.member_id, project.project_id, "One too many", None)
        self.assertEqual(raised.exception.code, "task_limit_reached")

        self.workspace.move_task_to_status(
            self.member_id,
            self.workspace.list_tasks(self.member_id, None, project.project_id, None)[0]["task_id"],
            completion.status_id,
        )
        replacement = self.workspace.create_task(self.member_id, project.project_id, "Capacity restored", None)
        self.assertEqual(replacement["name"], "Capacity restored")
