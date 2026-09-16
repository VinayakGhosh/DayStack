from pydantic import BaseModel
import enum

class FeatureNameEnum(str, enum.Enum):
    TASK = "Task"

class StatsResponse(BaseModel):
    projects_count: int
    tasks_count: int
    tasks_completed_count: int
    tasks_pending_count: int
    tasks_in_progress_count: int
    task_limit: int
    project_limit: int
   