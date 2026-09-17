"""Behavior tests for MVP Task details, Labels, Subtasks, and active-task quota."""

from test_project_workflows import ProjectWorkflowTests

from task_workspace.sqlalchemy_repository import WorkspaceTaskLimitReached


class TaskDetailsTests(ProjectWorkflowTests):
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
