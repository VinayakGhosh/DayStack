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


router = APIRouter()

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

@router.post("/", response_model=ProjectCreateResponse)
def create_project(
    payload: CreateProject,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    subscription=Depends(require_active_subscription),
):
    user_plan = db.query(Plans).filter(Plans.plan_id == subscription.plan_id).first()
    if not user_plan:
        raise HTTPException(status_code=404, detail="No plan exists for this subscription")

    total_projects = (
        db.query(Projects).filter(
            Projects.owner_user_id == current_user.user_id,
            Projects.organization_id.is_(None),
            Projects.isDelete == False,
        ).count()
    )

    if user_plan.max_projects >= 0 and total_projects >= user_plan.max_projects:
        raise HTTPException(status_code=403, detail="Project limit reached for your current plan")

    new_project = Projects(
        owner_user_id=current_user.user_id,
        organization_id=None,
        name=payload.name,
        description=payload.description,
    )
    db.add(new_project)
    db.flush()

    _seed_default_statuses(db, new_project.project_id)
    db.commit()
    db.refresh(new_project)
    return new_project


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


@router.patch("/{project_id}", response_model=ProjectCreateResponse)
def update_project_details(
    payload: PatchProject,
    project_id: UUID4 = Path(..., description="project_id of the project"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    user_project = _get_project_or_404(db, project_id)

    if user_project.organization_id:
        organization = db.query(Organization).filter(
            Organization.organization_id == user_project.organization_id
        ).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        ensure_org_owner_or_admin(db, organization, current_user.user_id)
    else:
        if user_project.owner_user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to update this project")

    if payload.name is not None:
        user_project.name = payload.name
    if payload.description is not None:
        user_project.description = payload.description

    db.commit()
    db.refresh(user_project)
    return user_project


@router.get("/", response_model=List[ProjectResponse])
def get_project(
    project_id: Optional[UUID4] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    done_status = db.query(ProjectStatus).join(
        Projects, ProjectStatus.project_id == Projects.project_id
    ).filter(
        Projects.owner_user_id == current_user.user_id,
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
            Projects.owner_user_id == current_user.user_id,
            Projects.organization_id == None,
            Projects.isDelete == False,
        )
        .group_by(Projects.project_id)
    )

    if project_id is not None:
        query = query.filter(Projects.project_id == project_id)

    results = query.all()

    if not results:
        raise HTTPException(status_code=404, detail="No projects found for the user")

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
    user_project = _get_project_or_404(db, project_id)

    if user_project.organization_id:
        organization = db.query(Organization).filter(
            Organization.organization_id == user_project.organization_id
        ).first()
        if not organization:
            raise HTTPException(status_code=404, detail="Organization not found")
        ensure_org_owner_or_admin(db, organization, current_user.user_id)
    else:
        if user_project.owner_user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Not authorized to delete this project")

    user_project.isDelete = True
    db.commit()
    return


# ---------------------------------------------------------------------------
# Project Status endpoints
# ---------------------------------------------------------------------------

@router.get("/{project_id}/statuses", response_model=List[ProjectStatusResponse])
def get_project_statuses(
    project_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _get_project_or_404(db, project_id)

    statuses = db.query(ProjectStatus).filter(
        ProjectStatus.project_id == project_id
    ).order_by(ProjectStatus.created_at).all()

    return statuses


@router.post("/{project_id}/statuses", response_model=ProjectStatusResponse)
def create_project_status(
    payload: CreateProjectStatus,
    project_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)

    if project.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage statuses for this project")

    new_status = ProjectStatus(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
    )
    db.add(new_status)
    db.commit()
    db.refresh(new_status)
    return new_status


@router.patch("/{project_id}/statuses/{status_id}", response_model=ProjectStatusResponse)
def update_project_status(
    payload: PatchProjectStatus,
    project_id: UUID4 = Path(...),
    status_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)

    if project.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage statuses for this project")

    status = db.query(ProjectStatus).filter(
        ProjectStatus.status_id == status_id,
        ProjectStatus.project_id == project_id,
    ).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    old_name = status.name

    if payload.name is not None:
        status.name = payload.name
    if payload.description is not None:
        status.description = payload.description

    if payload.name is not None and payload.name != old_name:
        affected_tasks = db.query(Tasks).filter(
            Tasks.project_id == project_id,
            Tasks.status_id == status_id,
            Tasks.isDelete == False,
        ).all()

        for task in affected_tasks:
            db.add(TaskStatusHistory(
                task_id=task.task_id,
                old_status_id=status_id,
                old_status_name=old_name,
                new_status_id=status_id,
                new_status_name=payload.name,
                changed_by=current_user.user_id,
            ))
            task.status_name = payload.name

    db.commit()
    db.refresh(status)
    return status


@router.delete("/{project_id}/statuses/{status_id}", status_code=204)
def delete_project_status(
    project_id: UUID4 = Path(...),
    status_id: UUID4 = Path(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    project = _get_project_or_404(db, project_id)

    if project.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to manage statuses for this project")

    status = db.query(ProjectStatus).filter(
        ProjectStatus.status_id == status_id,
        ProjectStatus.project_id == project_id,
    ).first()
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")

    tasks_using = db.query(Tasks).filter(
        Tasks.status_id == status_id,
        Tasks.isDelete == False,
    ).count()
    if tasks_using > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete status: {tasks_using} task(s) are currently using it",
        )

    db.delete(status)
    db.commit()
    return
