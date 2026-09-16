from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class TaskCreateSchema(BaseModel):
    project_id: UUID
    name: str
    description: Optional[str] = None
    assigned_to: Optional[UUID] = None


class TaskResponseSchema(BaseModel):
    task_id: UUID
    project_id: UUID
    status_id: Optional[UUID]
    status_name: Optional[str]
    created_by: UUID
    assigned_to: Optional[UUID]
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PatchTask(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class PatchTaskStatus(BaseModel):
    status_id: UUID


class MoveTaskStatusResponse(BaseModel):
    task_id: UUID
    status_id: Optional[UUID]
    status_name: Optional[str]

    class Config:
        from_attributes = True