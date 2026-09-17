from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class CreateProject(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreateResponse(BaseModel):
    project_id: UUID
    owner_user_id: UUID
    organization_id: Optional[UUID]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    project_id: UUID
    owner_user_id: UUID
    organization_id: Optional[UUID]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime
    total_tasks: int
    completed_tasks: int

    class Config:
        from_attributes = True


class PatchProject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectStatusResponse(BaseModel):
    status_id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    is_completion: bool
    display_order: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateProjectStatus(BaseModel):
    name: str
    description: Optional[str] = None


class PatchProjectStatus(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_completion: Optional[bool] = None


class ReorderProjectStatuses(BaseModel):
    status_ids: list[UUID]


class DeleteProjectStatus(BaseModel):
    reassign_to_status_id: Optional[UUID] = None


class ProjectQuotaResponse(BaseModel):
    used: int
    limit: int
    remaining: int
