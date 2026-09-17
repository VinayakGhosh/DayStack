from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.db import get_db
from lib.auth import get_current_user
from schema.today import TodayReorderInput, TodayResponse, TodayTaskInput
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import SqlAlchemyTaskWorkspaceRepository, WorkspaceProblem


router = APIRouter()


def _workspace(db: Session) -> TaskWorkspace:
    return TaskWorkspace(SqlAlchemyTaskWorkspaceRepository(db))


def _raise_workspace_error(error: WorkspaceProblem) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail={"code": error.code, "message": str(error)},
    ) from error


@router.get("/", response_model=TodayResponse)
def get_today(
    local_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).get_today(current_user.user_id, local_date)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.post("/tasks", response_model=TodayResponse)
def add_today_task(
    payload: TodayTaskInput,
    local_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).add_today_task(current_user.user_id, payload.task_id, local_date)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.delete("/tasks/{task_id}", status_code=204)
def remove_today_task(
    task_id: UUID,
    local_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        _workspace(db).remove_today_task(current_user.user_id, task_id, local_date)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.put("/tasks/reorder", response_model=TodayResponse)
def reorder_today_tasks(
    payload: TodayReorderInput,
    local_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).reorder_today_tasks(current_user.user_id, payload.task_ids, local_date)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)
