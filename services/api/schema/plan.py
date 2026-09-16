from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class PlanCreate(BaseModel):
    plan_tier: str
    price: int
    duration_days: Optional[int]
    max_projects: int
    task_per_day: int
    export_allowed: bool

class PlanResponse(BaseModel):
    plan_id: UUID
    plan_tier: str
    price: Optional[int]
    duration_days: Optional[int]
    max_projects: int
    task_per_day: int
    export_allowed: bool
    class Config:
        from_attributes = True

