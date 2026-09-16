from fastapi import HTTPException, Depends, APIRouter, Path, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.db import get_db
from lib.auth import get_current_user
from lib.subscription import require_active_subscription
from models.plan import Plans
from models.Project import Projects, ProjectStatus
from models.Task import Tasks, TaskStatusHistory
from models.organization import Organization, OrganizationMember
from schema.project import (
    ProjectResponse,
    CreateProject,
    PatchProject,
    ProjectCreateResponse,
    ProjectStatusResponse,
    CreateProjectStatus,
    PatchProjectStatus,
)
from pydantic import UUID4
from typing import List, Optional
from task_workspace.service import TaskWorkspace
from task_workspace.sqlalchemy_repository import (
    SqlAlchemyTaskWorkspaceRepository,
    WorkspaceConflict,
    WorkspaceForbidden,
    WorkspaceNotFound,
)


router = APIRouter()


def _workspace(db: Session) -> TaskWorkspace:
    return TaskWorkspace(SqlAlchemyTaskWorkspaceRepository(db))


def _raise_workspace_error(error: Exception) -> None:
    if isinstance(error, WorkspaceConflict):
        raise HTTPException(status_code=409, detail=str(error)) from error
    if isinstance(error, WorkspaceForbidden):
        raise HTTPException(status_code=403, detail=str(error)) from error
    raise HTTPException(status_code=404, detail=str(error)) from error


def _project_response(result) -> ProjectResponse:
    project, total_tasks, completed_tasks = result
    return ProjectResponse(
        project_id=project.project_id,
        owner_user_id=project.owner_user_id,
        organization_id=project.organization_id,
        name=project.name,
        description=project.description,
        created_at=project.created_at,
        updated_at=project.updated_at,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
    )

DEFAULT_STATUSES = [
    {"name": "Todo", "description": "Task is not yet started"},
    {"name": "In Progress", "description": "Task is actively being worked on"},
    {"name": "Done", "description": "Task has been completed"},
]


def ensure_org_owner_or_admin(db: Session, organization: Organization, user_id: UUID4):
    if organization.owner_id == user_id:
        return

    membership = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization.organization_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )

    if not membership or membership.role.lower() != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only organization owner or admin can perform this action",
        )


def _seed_default_statuses(db: Session, project_id):
    for s in DEFAULT_STATUSES:
        db.add(ProjectStatus(project_id=project_id, name=s["name"], description=s["description"]))


def _get_project_or_404(db: Session, project_id):
    project = db.query(Projects).filter(
        Projects.project_id == project_id,
        Projects.isDelete == False,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=ProjectResponse)
def create_project(
    payload: CreateProject,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    workspace = _workspace(db)
    project = workspace.create_project(current_user.user_id, payload.name, payload.description)
    return _project_response(workspace.get_project(current_user.user_id, project.project_id))


@router.post("/organization", response_model=ProjectCreateResponse)
def create_project_organization(
    payload: CreateProject,
    organization_id: UUID4 = Query(..., description="Organization ID to create project for"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    subscription=Depends(require_active_subscription),
):
    organization = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    ensure_org_owner_or_admin(db, organization, current_user.user_id)

    user_plan = db.query(Plans).filter(Plans.plan_id == subscription.plan_id).first()
    if not user_plan:
        raise HTTPException(status_code=404, detail="No plan exists for this subscription")

    total_projects = (
        db.query(Projects).filter(
            Projects.organization_id == organization_id
        ).count()
    )

    if user_plan.max_projects >= 0 and total_projects >= user_plan.max_projects:
        raise HTTPException(status_code=403, detail="Project limit reached for your current plan")

    new_project = Projects(
        owner_user_id=organization.owner_id,
        organization_id=organization_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(new_project)
    db.flush()

    _seed_default_statuses(db, new_project.project_id)
    db.commit()
    db.refresh(new_project)
    return new_project


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
    project_id: Optional[UUID4] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    results = _workspace(db).list_projects(current_user.user_id)
    if project_id is not None:
        results = [result for result in results if result[0].project_id == project_id]

    response = []
    for project, total_tasks, completed_tasks in results:
        response.append(_project_response((project, total_tasks, completed_tasks)))
    return response


@router.get("/organization", response_model=List[ProjectResponse])
def get_project_organization(
    organization_id: UUID4 = Query(..., description="Organization ID to fetch projects for"),
    project_id: Optional[UUID4] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    organization = db.query(Organization).filter(
        Organization.organization_id == organization_id
    ).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")

    organization_member = db.query(OrganizationMember).filter(
        OrganizationMember.organization_id == organization_id,
        OrganizationMember.user_id == current_user.user_id,
    ).first()
    if current_user.user_id != organization.owner_id and not organization_member:
        raise HTTPException(status_code=403, detail="Not a member of this organization")

    done_status = db.query(ProjectStatus).join(
        Projects, ProjectStatus.project_id == Projects.project_id
    ).filter(
        Projects.organization_id == organization_id,
        func.lower(ProjectStatus.name) == "done",
    ).subquery()

    query = (
        db.query(
            Projects,
            func.count(Tasks.task_id).label("total_tasks"),
            func.count(Tasks.task_id)
                .filter(Tasks.status_id == done_status.c.status_id)
                .label("completed_tasks"),
        )
        .outerjoin(Tasks, (Tasks.project_id == Projects.project_id) & (Tasks.isDelete == False))
        .filter(
            Projects.organization_id == organization_id,
            Projects.isDelete == False,
        )
        .group_by(Projects.project_id)
    )

    if project_id is not None:
        query = query.filter(Projects.project_id == project_id)

    results = query.all()
    if not results:
        raise HTTPException(status_code=404, detail="No projects found for the organization")

    response = []
    for project, total_tasks, completed_tasks in results:
        response.append(
            ProjectResponse(
                project_id=project.project_id,
                owner_user_id=project.owner_user_id,
                organization_id=project.organization_id,
                name=project.name,
                description=project.description,
                created_at=project.created_at,
                updated_at=project.updated_at,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
            )
        )
    return response


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
            current_user.user_id, project_id, status_id, payload.name, payload.description
        )
    except (WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)


@router.delete("/{project_id}/statuses/{status_id}", status_code=204)
def delete_project_status(
    project_id: UUID4 = Path(...),
    status_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        _workspace(db).delete_status(current_user.user_id, project_id, status_id)
    except (WorkspaceConflict, WorkspaceForbidden, WorkspaceNotFound) as error:
        _raise_workspace_error(error)
