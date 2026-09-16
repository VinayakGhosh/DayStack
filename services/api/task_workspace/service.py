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
