from datetime import date
from uuid import UUID

from pydantic import BaseModel

from schema.task import TaskResponseSchema


class TodayTaskInput(BaseModel):
    task_id: UUID


class TodayReorderInput(BaseModel):
    task_ids: list[UUID]


class TodaySelectedTaskResponse(BaseModel):
    position: int
    task: TaskResponseSchema


class TodayResponse(BaseModel):
    local_date: date
    selected_tasks: list[TodaySelectedTaskResponse]
    due_today: list[TaskResponseSchema]
    overdue: list[TaskResponseSchema]
    available_tasks: list[TaskResponseSchema]
