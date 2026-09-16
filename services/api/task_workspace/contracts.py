"""Ports used by Task Workspace; infrastructure stays behind these boundaries."""

from typing import Protocol
from uuid import UUID


class TaskWorkspaceRepository(Protocol):
    def list_projects(self, member_id: UUID): ...

    def create_project(self, member_id: UUID, name: str, description: str | None): ...


class TaskWorkspaceStorage(Protocol):
    def delete_task_files(self, task_id: UUID) -> None: ...

    def delete_project_files(self, project_id: UUID) -> None: ...
