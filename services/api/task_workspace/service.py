"""Member-visible Project, Task, and Workflow status operations."""

from uuid import UUID

from .contracts import TaskWorkspaceRepository


class TaskWorkspace:
    """Coordinates personal work without exposing persistence to route handlers."""

    def __init__(self, repository: TaskWorkspaceRepository):
        self._repository = repository

    def list_projects(self, member_id: UUID):
        return self._repository.list_projects(member_id)

    def get_project(self, member_id: UUID, project_id: UUID):
        return self._repository.get_project(member_id, project_id)

    def create_project(self, member_id: UUID, name: str, description: str | None):
        return self._repository.create_project(member_id, name, description)

    def project_quota(self, member_id: UUID):
        return self._repository.project_quota(member_id)

    def move_task_to_status(self, member_id: UUID, task_id: UUID, status_id: UUID):
        return self._repository.move_task_to_status(member_id, task_id, status_id)

    def update_project(self, member_id: UUID, project_id: UUID, name: str | None, description: str | None):
        return self._repository.update_project(member_id, project_id, name, description)

    def delete_project(self, member_id: UUID, project_id: UUID):
        return self._repository.delete_project(member_id, project_id)

    def list_statuses(self, member_id: UUID, project_id: UUID):
        return self._repository.list_statuses(member_id, project_id)

    def create_status(self, member_id: UUID, project_id: UUID, name: str, description: str | None):
        return self._repository.create_status(member_id, project_id, name, description)

    def update_status(
        self,
        member_id: UUID,
        project_id: UUID,
        status_id: UUID,
        name: str | None,
        description: str | None,
        is_completion: bool | None = None,
    ):
        return self._repository.update_status(
            member_id, project_id, status_id, name, description, is_completion
        )

    def reorder_statuses(self, member_id: UUID, project_id: UUID, status_ids: list[UUID]):
        return self._repository.reorder_statuses(member_id, project_id, status_ids)

    def delete_status(
        self,
        member_id: UUID,
        project_id: UUID,
        status_id: UUID,
        reassign_to_status_id: UUID | None = None,
    ):
        return self._repository.delete_status(
            member_id, project_id, status_id, reassign_to_status_id
        )

    def create_task(self, member_id: UUID, project_id: UUID, name: str, description: str | None, due_date=None, priority: str = "none", label_ids=None, subtasks=None):
        return self._repository.create_task(member_id, project_id, name, description, due_date, priority, label_ids, subtasks)

    def update_task(self, member_id: UUID, task_id: UUID, name: str | None, description: str | None, due_date=None, priority: str | None = None, label_ids=None, subtasks=None, updated_fields=None):
        return self._repository.update_task(member_id, task_id, name, description, due_date, priority, label_ids, subtasks, updated_fields)

    def list_tasks(self, member_id: UUID, task_id: UUID | None, project_id: UUID | None, status_id: UUID | None):
        return self._repository.list_tasks(member_id, task_id, project_id, status_id)

    def delete_task(self, member_id: UUID, task_id: UUID):
        return self._repository.delete_task(member_id, task_id)

    def set_task_status(self, member_id: UUID, task_id: UUID, status_id: UUID):
        return self._repository.set_task_status(member_id, task_id, status_id)

    def task_quota(self, member_id: UUID, project_id: UUID):
        return self._repository.task_quota(member_id, project_id)

    def list_labels(self, member_id: UUID):
        return self._repository.list_labels(member_id)

    def create_label(self, member_id: UUID, name: str, color: str | None):
        return self._repository.create_label(member_id, name, color)

    def update_label(self, member_id: UUID, label_id: UUID, name: str | None, color: str | None):
        return self._repository.update_label(member_id, label_id, name, color)

    def delete_label(self, member_id: UUID, label_id: UUID):
        return self._repository.delete_label(member_id, label_id)

    def set_subtasks(self, member_id: UUID, task_id: UUID, subtasks: list[dict]):
        return self._repository.set_subtasks(member_id, task_id, subtasks)

    def toggle_subtask(self, member_id: UUID, task_id: UUID, subtask_id: UUID, is_completed: bool):
        return self._repository.toggle_subtask(member_id, task_id, subtask_id, is_completed)

    def get_today(self, member_id: UUID, local_date):
        return self._repository.get_today(member_id, local_date)

    def add_today_task(self, member_id: UUID, task_id: UUID, local_date):
        return self._repository.add_today_task(member_id, task_id, local_date)

    def remove_today_task(self, member_id: UUID, task_id: UUID, local_date):
        return self._repository.remove_today_task(member_id, task_id, local_date)

    def reorder_today_tasks(self, member_id: UUID, task_ids: list[UUID], local_date):
        return self._repository.reorder_today_tasks(member_id, task_ids, local_date)
