from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


Priority = Literal["none", "low", "medium", "high"]


class LabelInput(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=32)


class LabelResponse(LabelInput):
    label_id: UUID


class PatchLabel(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=32)


class SubtaskInput(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    is_completed: bool = False


class SubtaskResponse(SubtaskInput):
    subtask_id: UUID
    display_order: int


class ToggleSubtask(BaseModel):
    is_completed: bool


class TaskCreateSchema(BaseModel):
    project_id: UUID
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    priority: Priority = "none"
    label_ids: list[UUID] = []
    subtasks: list[SubtaskInput] = []


class TaskResponseSchema(BaseModel):
    task_id: UUID
    project_id: UUID
    status_id: UUID | None
    status_name: str | None
    created_by: UUID
    name: str
    description: str | None
    due_date: date | None
    priority: Priority
    labels: list[LabelResponse]
    subtasks: list[SubtaskResponse]
    created_at: datetime
    updated_at: datetime

class PatchTask(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    due_date: date | None = None
    priority: Priority | None = None
    label_ids: list[UUID] | None = None
    subtasks: list[SubtaskInput] | None = None


class PatchTaskStatus(BaseModel):
    status_id: UUID


class TaskQuotaResponse(BaseModel):
    used: int
    limit: int
    remaining: int
