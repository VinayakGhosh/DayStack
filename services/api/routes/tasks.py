from fastapi import HTTPException, Depends, APIRouter, Query, Path
from sqlalchemy.orm import Session, aliased
from db.db import get_db
from lib.auth import get_current_user
from lib.subscription import require_active_subscription
from models.plan import Plans
from models.Project import Projects, ProjectStatus
from models.Task import Tasks, TaskStatusHistory
from models.user import Users, Usage
from schema.task import TaskCreateSchema, TaskResponseSchema, PatchTask, PatchTaskStatus, MoveTaskStatusResponse
from schema.stats import FeatureNameEnum
from datetime import datetime, timezone
from typing import Optional, List
from uuid import UUID

router = APIRouter()


def _get_task_with_ownership(db: Session, task_id, user_id):
    task = (
        db.query(Tasks)
        .join(Projects, Tasks.project_id == Projects.project_id)
        .filter(
            Tasks.task_id == task_id,
            Tasks.isDelete == False,
            Projects.owner_user_id == user_id,
            Projects.isDelete == False,
        )
        .first()
    )
    return task


def _build_task_response(task: Tasks, db: Session) -> dict:
    status_name = None
    if task.status_id:
        status_row = db.query(ProjectStatus).filter(
            ProjectStatus.status_id == task.status_id
        ).first()
        status_name = status_row.name if status_row else None

    return TaskResponseSchema(
        task_id=task.task_id,
        project_id=task.project_id,
        status_id=task.status_id,
        status_name=status_name,
        created_by=task.created_by,
        assigned_to=task.assigned_to,
        name=task.name,
        description=task.description,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


##### CRUD Operations #####

@router.post("/", response_model=TaskResponseSchema)
def create_task(
    payload: TaskCreateSchema,
    db: Session = Depends(get_db),
    subscription=Depends(require_active_subscription),
    current_user=Depends(get_current_user),
):
    project = db.query(Projects).filter(
        Projects.project_id == payload.project_id,
        Projects.owner_user_id == current_user.user_id,
        Projects.isDelete == False,
    ).first()

    if not project:
        raise HTTPException(status_code=403, detail="Invalid project")

    if payload.assigned_to is not None:
        assigned_user = db.query(Users).filter(Users.user_id == payload.assigned_to).first()
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    user_plan = db.query(Plans).filter(Plans.plan_id == subscription.plan_id).first()
    if not user_plan:
        raise HTTPException(status_code=404, detail="No plan found for this subscription")

    task_per_day = user_plan.task_per_day
    today = datetime.now(timezone.utc).date()

    usage_today = db.query(Usage).filter(
        Usage.date == today,
        Usage.feature_name == FeatureNameEnum.TASK.value,
        Usage.user_id == current_user.user_id,
    ).first()

    if usage_today:
        if task_per_day >= 0 and usage_today.feature_count >= task_per_day:
            raise HTTPException(status_code=403, detail="Task limit exceeded for today")
        usage_today.feature_count += 1
    else:
        db.add(Usage(
            user_id=current_user.user_id,
            feature_name=FeatureNameEnum.TASK.value,
            feature_count=1,
            date=today,
        ))

    todo_status = db.query(ProjectStatus).filter(
        ProjectStatus.project_id == payload.project_id,
        ProjectStatus.name.ilike("todo"),
    ).first()

    new_task = Tasks(
        project_id=payload.project_id,
        created_by=current_user.user_id,
        assigned_to=payload.assigned_to,
        status_id=todo_status.status_id if todo_status else None,
        status_name=todo_status.name if todo_status else None,
        name=payload.name,
        description=payload.description,
    )

    db.add(new_task)
    db.flush()

    new_task_history = TaskStatusHistory(
        task_id=new_task.task_id,
        old_status_id=None,
        old_status_name=None,
        new_status_id=todo_status.status_id if todo_status else None,
        new_status_name=todo_status.name if todo_status else None,
        changed_by=current_user.user_id,
    )
    db.add(new_task_history)

    db.commit()
    db.refresh(new_task)
    return _build_task_response(new_task, db)


@router.patch("/{task_id}", response_model=TaskResponseSchema)
def update_task(
    task_id: UUID,
    payload: PatchTask,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = _get_task_with_ownership(db, task_id, current_user.user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if payload.name is not None:
        task.name = payload.name
    if payload.description is not None:
        task.description = payload.description

    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)




@router.get("/", response_model=List[TaskResponseSchema])
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    task_id: Optional[UUID] = Query(None),
    project_id: Optional[UUID] = Query(None),
    status_id: Optional[UUID] = Query(None),
):
    query = (
        db.query(Tasks)
        .join(Projects, Tasks.project_id == Projects.project_id)
        .filter(
            Projects.owner_user_id == current_user.user_id,
            Projects.isDelete == False,
            Tasks.isDelete == False,
        )
    )

    if task_id is not None:
        query = query.filter(Tasks.task_id == task_id)
    if project_id is not None:
        query = query.filter(Tasks.project_id == project_id)
    if status_id is not None:
        query = query.filter(Tasks.status_id == status_id)

    tasks = query.order_by(Tasks.created_at.desc()).all()
    return [_build_task_response(t, db) for t in tasks]


@router.delete("/{task_id}", status_code=204)
def delete_task(
    task_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = _get_task_with_ownership(db, task_id, current_user.user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.isDelete = True
    db.commit()
    return


##### Status Operations #####

@router.patch("/{task_id}/status", response_model=TaskResponseSchema)
def update_task_status(
    task_id: UUID,
    payload: PatchTaskStatus,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = _get_task_with_ownership(db, task_id, current_user.user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    status = db.query(ProjectStatus).filter(
        ProjectStatus.status_id == payload.status_id,
        ProjectStatus.project_id == task.project_id,
    ).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found or does not belong to this project")

    task.status_id = payload.status_id
    task.status_name = status.name
    db.commit()
    db.refresh(task)
    return _build_task_response(task, db)


@router.post("/{task_id}/move", response_model=MoveTaskStatusResponse)
def move_task_to_new_status(
    task_id: UUID,
    payload: PatchTaskStatus,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    task = _get_task_with_ownership(db, task_id, current_user.user_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    new_status = db.query(ProjectStatus).filter(
        ProjectStatus.status_id == payload.status_id,
        ProjectStatus.project_id == task.project_id,
    ).first()
    if not new_status:
        raise HTTPException(status_code=404, detail="Status not found or does not belong to this project")

    history = TaskStatusHistory(
        task_id=task.task_id,
        old_status_id=task.status_id,
        old_status_name=task.status_name,
        new_status_id=new_status.status_id,
        new_status_name=new_status.name,
        changed_by=current_user.user_id,
    )
    db.add(history)

    task.status_id = new_status.status_id
    task.status_name = new_status.name

    db.commit()
    db.refresh(task)
    return MoveTaskStatusResponse(
        task_id=task.task_id,
        status_id=task.status_id,
        status_name=task.status_name,
    )
