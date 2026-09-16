from pydantic import BaseModel
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
import enum


class SubscriptionStatusEnum(str, enum.Enum):
    ACTIVE = "Active"
    CANCELLED = "Cancelled"
    EXPIRED = "Expired"
    ENDED = "Ended"  # when new plan subscription added above and existing one


class SubscriptionCreate(BaseModel):
    user_id: UUID
    plan_id: UUID
    start_timestamp: datetime
    end_timestamp: Optional[datetime]
    status: SubscriptionStatusEnum


class SubscriptionResponse(BaseModel):
    subscription_id: UUID
    user_id: UUID
    plan_id: UUID
    start_timestamp: datetime
    end_timestamp: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # IMPORTANT for SQLAlchemy ORM

class PlanFeatures(BaseModel):
    project: int
    task: int
    export_allowed: bool


class CurrentSubscriptionResponse(BaseModel):
    id: UUID
    plan_id: UUID
    plan_name: str
    status: SubscriptionStatusEnum
    current_period_start: datetime
    current_period_end: datetime
    max_projects: int
    task_per_day: int
    export_allowed: bool
    features: PlanFeatures
    days_left: Optional[int] = None

