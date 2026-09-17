from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from db.db import get_db
from lib.auth import get_current_user
from schema.task import (
    LabelInput,
    LabelResponse,
    PatchLabel,
    PatchTask,
    PatchTaskStatus,
    SubtaskInput,
    SubtaskResponse,
    TaskCreateSchema,
    TaskQuotaResponse,
    TaskResponseSchema,
    ToggleSubtask,
)
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import (
    SqlAlchemyTaskWorkspaceRepository,
    WorkspaceForbidden,
    WorkspaceNotFound,
    WorkspaceProblem,
)

router = APIRouter()


def _workspace(db: Session) -> TaskWorkspace:
    return TaskWorkspace(SqlAlchemyTaskWorkspaceRepository(db))


def _raise_workspace_error(error: Exception) -> None:
    if isinstance(error, WorkspaceProblem):
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": str(error)},
        ) from error
    raise error


def _subtasks(items: list[SubtaskInput] | None):
    return [item.model_dump() for item in items] if items is not None else None


@router.post("/", response_model=TaskResponseSchema)
def create_task(
    payload: TaskCreateSchema,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).create_task(
            current_user.user_id, payload.project_id, payload.name, payload.description,
            payload.due_date, payload.priority, payload.label_ids, _subtasks(payload.subtasks),
        )
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.patch("/{task_id}", response_model=TaskResponseSchema)
def update_task(task_id: UUID, payload: PatchTask, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).update_task(
            current_user.user_id, task_id, payload.name, payload.description,
            payload.due_date, payload.priority, payload.label_ids, _subtasks(payload.subtasks),
            payload.model_fields_set,
        )
    except WorkspaceProblem as error:
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
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.patch("/{task_id}/status", response_model=TaskResponseSchema)
def update_task_status(
    task_id: UUID, payload: PatchTaskStatus, db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).set_task_status(current_user.user_id, task_id, payload.status_id)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.post("/{task_id}/move", response_model=TaskResponseSchema)
def move_task_to_new_status(
    task_id: UUID, payload: PatchTaskStatus, db: Session = Depends(get_db), current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).move_task_to_status(current_user.user_id, task_id, payload.status_id)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.get("/project/{project_id}/usage", response_model=TaskQuotaResponse)
def get_task_quota(project_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).task_quota(current_user.user_id, project_id)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.get("/labels/", response_model=List[LabelResponse])
def get_labels(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return _workspace(db).list_labels(current_user.user_id)


@router.post("/labels/", response_model=LabelResponse)
def create_label(payload: LabelInput, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).create_label(current_user.user_id, payload.name, payload.color)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.patch("/labels/{label_id}", response_model=LabelResponse)
def update_label(label_id: UUID, payload: PatchLabel, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).update_label(current_user.user_id, label_id, payload.name, payload.color)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.delete("/labels/{label_id}", status_code=204)
def delete_label(label_id: UUID, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        _workspace(db).delete_label(current_user.user_id, label_id)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.put("/{task_id}/subtasks", response_model=TaskResponseSchema)
def set_subtasks(task_id: UUID, payload: List[SubtaskInput], db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).set_subtasks(current_user.user_id, task_id, _subtasks(payload) or [])
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.patch("/{task_id}/subtasks/{subtask_id}", response_model=SubtaskResponse)
def toggle_subtask(task_id: UUID, subtask_id: UUID, payload: ToggleSubtask, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        return _workspace(db).toggle_subtask(current_user.user_id, task_id, subtask_id, payload.is_completed)
    except WorkspaceProblem as error:
        _raise_workspace_error(error)
