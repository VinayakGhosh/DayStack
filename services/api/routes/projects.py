from fastapi import HTTPException, Depends, APIRouter, Path
from sqlalchemy.orm import Session
from db.db import get_db
from lib.auth import get_current_user
from schema.project import (
    ProjectResponse,
    CreateProject,
    PatchProject,
    ProjectStatusResponse,
    CreateProjectStatus,
    DeleteProjectStatus,
    PatchProjectStatus,
    ProjectQuotaResponse,
    ReorderProjectStatuses,
)
from pydantic import UUID4
from typing import List
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import (
    SqlAlchemyTaskWorkspaceRepository,
    WorkspaceConflict,
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


def _project_response(result) -> ProjectResponse:
    project, total_tasks, completed_tasks = result
    return ProjectResponse(
        project_id=project.project_id,
        owner_user_id=project.owner_user_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
    )

@router.post("/", response_model=ProjectResponse)
def create_project(
    payload: CreateProject,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        workspace = _workspace(db)
        project = workspace.create_project(current_user.user_id, payload.name, payload.description)
        return _project_response(workspace.get_project(current_user.user_id, project.project_id))
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project_details(
    payload: PatchProject,
    project_id: UUID4 = Path(..., description="project_id of the project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        workspace = _workspace(db)
        project = workspace.update_project(
            current_user.user_id, project_id, payload.name, payload.description
        )
        return _project_response(workspace.get_project(current_user.user_id, project.project_id))
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.get("/", response_model=List[ProjectResponse])
def get_project(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    results = _workspace(db).list_projects(current_user.user_id)
    response = []
    for project, total_tasks, completed_tasks in results:
        response.append(_project_response((project, total_tasks, completed_tasks)))
    return response


@router.get("/usage", response_model=ProjectQuotaResponse)
def get_project_quota(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return _workspace(db).project_quota(current_user.user_id)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: UUID4 = Path(..., description="project_id of the project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        _workspace(db).delete_project(current_user.user_id, project_id)
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project_details(
    project_id: UUID4 = Path(..., description="project_id of the Project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _project_response(_workspace(db).get_project(current_user.user_id, project_id))
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


# ---------------------------------------------------------------------------
# Project Status endpoints
# ---------------------------------------------------------------------------

@router.get("/{project_id}/statuses", response_model=List[ProjectStatusResponse])
def get_project_statuses(
    project_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).list_statuses(current_user.user_id, project_id)
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.post("/{project_id}/statuses", response_model=ProjectStatusResponse)
def create_project_status(
    payload: CreateProjectStatus,
    project_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).create_status(
            current_user.user_id, project_id, payload.name, payload.description
        )
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.patch("/{project_id}/statuses/{status_id}", response_model=ProjectStatusResponse)
def update_project_status(
    payload: PatchProjectStatus,
    project_id: UUID4 = Path(...),
    status_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).update_status(
            current_user.user_id,
            project_id,
            status_id,
            payload.name,
            payload.description,
            payload.is_completion,
        )
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.put("/{project_id}/statuses/reorder", response_model=List[ProjectStatusResponse])
def reorder_project_statuses(
    payload: ReorderProjectStatuses,
    project_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return _workspace(db).reorder_statuses(
            current_user.user_id, project_id, payload.status_ids
        )
    except WorkspaceProblem as error:
        _raise_workspace_error(error)


@router.delete("/{project_id}/statuses/{status_id}", status_code=204)
def delete_project_status(
    project_id: UUID4 = Path(...),
    status_id: UUID4 = Path(...),
    payload: DeleteProjectStatus | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        _workspace(db).delete_status(
            current_user.user_id,
            project_id,
            status_id,
            payload.reassign_to_status_id if payload else None,
        )
    except WorkspaceProblem as error:
        _raise_workspace_error(error)
