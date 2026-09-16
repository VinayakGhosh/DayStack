"""Member-visible Project, Task, and Workflow status operations."""

from uuid import UUID

from .contracts import TaskWorkspaceRepository


class TaskWorkspace:
    """Coordinates personal work without exposing persistence to route handlers."""

    def __init__(self, repository: TaskWorkspaceRepository):
        self._repository = repository

    def list_projects(self, member_id: UUID):
        return self._repository.list_projects(member_id)

    def create_project(self, member_id: UUID, name: str, description: str | None):
        return self._repository.create_project(member_id, name, description)

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

    def update_status(self, member_id: UUID, project_id: UUID, status_id: UUID, name: str | None, description: str | None):
        return self._repository.update_status(member_id, project_id, status_id, name, description)

    def delete_status(self, member_id: UUID, project_id: UUID, status_id: UUID):
        return self._repository.delete_status(member_id, project_id, status_id)

    def create_task(self, member_id: UUID, project_id: UUID, assigned_to: UUID | None, name: str, description: str | None, plan_id: UUID):
        return self._repository.create_task(member_id, project_id, assigned_to, name, description, plan_id)

    def update_task(self, member_id: UUID, task_id: UUID, name: str | None, description: str | None):
        return self._repository.update_task(member_id, task_id, name, description)

    def list_tasks(self, member_id: UUID, task_id: UUID | None, project_id: UUID | None, status_id: UUID | None):
        return self._repository.list_tasks(member_id, task_id, project_id, status_id)

    def delete_task(self, member_id: UUID, task_id: UUID):
        return self._repository.delete_task(member_id, task_id)

    def set_task_status(self, member_id: UUID, task_id: UUID, status_id: UUID):
        return self._repository.set_task_status(member_id, task_id, status_id)
