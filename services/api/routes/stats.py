from models.plan import Plans
from models.Project import Projects, ProjectStatus
from models.Task import Tasks
from typing import Optional
from fastapi import HTTPException, Depends, Query, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.db import get_db
from lib.auth import get_current_user
from lib.subscription import require_active_subscription
from schema.stats import StatsResponse

router = APIRouter()

@router.get("/", response_model=StatsResponse)
def get_overall_stats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    subscription=Depends(require_active_subscription)
):
    # Calculate Projects Count
    projects_count = db.query(Projects).filter(
        Projects.owner_user_id == current_user.user_id,
        Projects.isDelete == False
    ).count()

    # Base task query: tasks belonging to projects owned by the current user
    base_task_query = (
        db.query(Tasks)
        .join(Projects, Tasks.project_id == Projects.project_id)
        .filter(
            Projects.owner_user_id == current_user.user_id,
            Projects.isDelete == False,
            Tasks.isDelete == False,
        )
    )

    tasks_count = base_task_query.count()

    # Resolve status IDs by name for this user's projects
    done_ids = db.query(ProjectStatus.status_id).join(
        Projects, ProjectStatus.project_id == Projects.project_id
    ).filter(
        Projects.owner_user_id == current_user.user_id,
        func.lower(ProjectStatus.name) == "done",
    ).subquery()

    todo_ids = db.query(ProjectStatus.status_id).join(
        Projects, ProjectStatus.project_id == Projects.project_id
    ).filter(
        Projects.owner_user_id == current_user.user_id,
        func.lower(ProjectStatus.name) == "todo",
    ).subquery()

    in_progress_ids = db.query(ProjectStatus.status_id).join(
        Projects, ProjectStatus.project_id == Projects.project_id
    ).filter(
        Projects.owner_user_id == current_user.user_id,
        func.lower(ProjectStatus.name) == "in progress",
    ).subquery()

    tasks_completed_count = base_task_query.filter(Tasks.status_id.in_(done_ids)).count()
    tasks_pending_count = base_task_query.filter(Tasks.status_id.in_(todo_ids)).count()
    tasks_in_progress_count = base_task_query.filter(Tasks.status_id.in_(in_progress_ids)).count()

    # Get plan limits from subscription
    plan = db.query(Plans).filter(
        Plans.plan_id == subscription.plan_id,
        Plans.is_deleted == False,
        Plans.is_discontinued == False
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="No active subscription plan found")

    return StatsResponse(
        projects_count=projects_count,
        tasks_count=tasks_count,
        tasks_completed_count=tasks_completed_count,
        tasks_pending_count=tasks_pending_count,
        tasks_in_progress_count=tasks_in_progress_count,
        task_limit=plan.task_per_day,
        project_limit=plan.max_projects
    )
