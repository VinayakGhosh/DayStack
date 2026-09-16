from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.db import get_db
from lib.auth import get_current_user
from lib.subscription import require_active_subscription
from schema.task import MoveTaskStatusResponse, PatchTask, PatchTaskStatus, TaskCreateSchema, TaskResponseSchema
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import (
    SqlAlchemyTaskWorkspaceRepository,
    WorkspaceForbidden,
    WorkspaceNotFound,
)

router = APIRouter()


def _workspace(db: Session) -> TaskWorkspace:
    return TaskWorkspace(SqlAlchemyTaskWorkspaceRepository(db))


def _raise_workspace_error(error: Exception) -> None:
    if isinstance(error, WorkspaceForbidden):
        raise HTTPException(status_code=403, detail=str(error)) from error
    raise HTTPException(status_code=404, detail=str(error)) from error


@router.post("/", response_model=TaskResponseSchema)
def create_task(
    payload: TaskCreateSchema,
    db: Session = Depends(get_db),
    subscription=Depends(require_active_subscription),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).create_task(
            current_user.user_id, payload.project_id, payload.assigned_to,
            payload.name, payload.description, subscription.plan_id,
        )
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.patch("/{task_id}", response_model=TaskResponseSchema)
def update_task(task_id: UUID, payload: PatchTask, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).update_task(current_user.user_id, task_id, payload.name, payload.description)
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.get("/", response_model=List[TaskResponseSchema])
def get_tasks(
    db: Session = Depends(get_db), current_user=Depends(get_current_user),
    task_id: Optional[UUID] = Query(None), project_id: Optional[UUID] = Query(None), status_id: Optional[UUID] = Query(None),
):
    return _workspace(db).list_tasks(current_user.user_id, task_id, project_id, status_id)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        _workspace(db).delete_task(current_user.user_id, task_id)
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.patch("/{task_id}/status", response_model=TaskResponseSchema)
def update_task_status(
    task_id: UUID, payload: PatchTaskStatus, db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).set_task_status(current_user.user_id, task_id, payload.status_id)
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.post("/{task_id}/move", response_model=MoveTaskStatusResponse)
def move_task_to_new_status(
    task_id: UUID, payload: PatchTaskStatus, db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).move_task_to_status(current_user.user_id, task_id, payload.status_id)
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)
