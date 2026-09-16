"""SQLAlchemy adapter for the Task Workspace port.

Only this adapter knows about ORM models.  HTTP handlers work with the
TaskWorkspace application service instead of mutating models directly.
"""

from datetime import datetime, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.Project import ProjectStatus, Projects
from models.Task import Tasks
from models.Task import TaskStatusHistory
from models.plan import Plans
from models.user import Usage, Users
from schema.stats import FeatureNameEnum


class WorkspaceNotFound(Exception):
    """The requested member-visible work item does not exist."""


class WorkspaceForbidden(Exception):
    """The member does not own the requested work item."""


class WorkspaceConflict(Exception):
    """The requested change conflicts with existing work."""


class SqlAlchemyTaskWorkspaceRepository:
    def __init__(self, db: Session):
        self._db = db

    def list_projects(self, member_id):
        done_statuses = (
            self._db.query(ProjectStatus.status_id)
            .join(Projects, ProjectStatus.project_id == Projects.project_id)
            .filter(
                Projects.owner_user_id == member_id,
                ProjectStatus.name.ilike("done"),
            )
            .subquery()
        )
        return self._db.query(
            Projects,
            func.count(Tasks.task_id).label("total_tasks"),
            func.count(Tasks.task_id)
            .filter(Tasks.status_id.in_(done_statuses))
            .label("completed_tasks"),
        ).outerjoin(
            Tasks,
            (Tasks.project_id == Projects.project_id) & (Tasks.isDelete == False),
        ).filter(
            Projects.owner_user_id == member_id,
            Projects.organization_id.is_(None),
            Projects.isDelete == False,
        ).group_by(Projects.project_id).all()

    def create_project(self, member_id, name, description):
        project = Projects(
            owner_user_id=member_id,
            organization_id=None,
            name=name,
            description=description,
        )
        self._db.add(project)
        self._db.flush()
        for status in (
            ("Todo", "Task is not yet started"),
            ("In Progress", "Task is actively being worked on"),
            ("Done", "Task has been completed"),
        ):
            self._db.add(ProjectStatus(project_id=project.project_id, name=status[0], description=status[1]))
        self._db.commit()
        self._db.refresh(project)
        return project

    def update_project(self, member_id, project_id, name, description):
        project = self._personal_project(member_id, project_id)
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        self._db.commit()
        self._db.refresh(project)
        return project

    def delete_project(self, member_id, project_id):
        project = self._personal_project(member_id, project_id)
        project.isDelete = True
        self._db.commit()

    def list_statuses(self, member_id, project_id):
        self._personal_project(member_id, project_id)
        return self._db.query(ProjectStatus).filter(
            ProjectStatus.project_id == project_id
        ).order_by(ProjectStatus.created_at).all()

    def create_status(self, member_id, project_id, name, description):
        self._personal_project(member_id, project_id)
        status = ProjectStatus(project_id=project_id, name=name, description=description)
        self._db.add(status)
        self._db.commit()
        self._db.refresh(status)
        return status

    def update_status(self, member_id, project_id, status_id, name, description):
        self._personal_project(member_id, project_id)
        status = self._status(project_id, status_id)
        old_name = status.name
        if name is not None:
            status.name = name
        if description is not None:
            status.description = description
        if name is not None and name != old_name:
            for task in self._db.query(Tasks).filter(
                Tasks.project_id == project_id,
                Tasks.status_id == status_id,
                Tasks.isDelete == False,
            ).all():
                self._db.add(TaskStatusHistory(
                    task_id=task.task_id,
                    old_status_id=status_id,
                    old_status_name=old_name,
                    new_status_id=status_id,
                    new_status_name=name,
                    changed_by=member_id,
                ))
                task.status_name = name
        self._db.commit()
        self._db.refresh(status)
        return status

    def delete_status(self, member_id, project_id, status_id):
        self._personal_project(member_id, project_id)
        status = self._status(project_id, status_id)
        tasks_using = self._db.query(Tasks).filter(
            Tasks.status_id == status_id,
            Tasks.isDelete == False,
        ).count()
        if tasks_using:
            raise WorkspaceConflict(f"Cannot delete status: {tasks_using} task(s) are currently using it")
        self._db.delete(status)
        self._db.commit()

    def create_task(self, member_id, project_id, assigned_to, name, description, plan_id):
        self._personal_project(member_id, project_id)
        if assigned_to is not None and not self._db.query(Users).filter(Users.user_id == assigned_to).first():
            raise WorkspaceNotFound("Assigned user not found")
        plan = self._db.query(Plans).filter(Plans.plan_id == plan_id).first()
        if not plan:
            raise WorkspaceNotFound("No plan found for this subscription")
        today = datetime.now(timezone.utc).date()
        usage = self._db.query(Usage).filter(
            Usage.date == today,
            Usage.feature_name == FeatureNameEnum.TASK.value,
            Usage.user_id == member_id,
        ).first()
        if usage and plan.task_per_day >= 0 and usage.feature_count >= plan.task_per_day:
            raise WorkspaceForbidden("Task limit exceeded for today")
        if usage:
            usage.feature_count += 1
        else:
            self._db.add(Usage(user_id=member_id, feature_name=FeatureNameEnum.TASK.value, feature_count=1, date=today))
        todo = self._db.query(ProjectStatus).filter(
            ProjectStatus.project_id == project_id,
            ProjectStatus.name.ilike("todo"),
        ).first()
        task = Tasks(project_id=project_id, created_by=member_id, assigned_to=assigned_to,
                     status_id=todo.status_id if todo else None, status_name=todo.name if todo else None,
                     name=name, description=description)
        self._db.add(task)
        self._db.flush()
        self._db.add(TaskStatusHistory(task_id=task.task_id, old_status_id=None, old_status_name=None,
                                       new_status_id=todo.status_id if todo else None,
                                       new_status_name=todo.name if todo else None, changed_by=member_id))
        self._db.commit()
        self._db.refresh(task)
        return self._task_response(task)

    def update_task(self, member_id, task_id, name, description):
        task = self._task(member_id, task_id)
        if name is not None:
            task.name = name
        if description is not None:
            task.description = description
        self._db.commit()
        self._db.refresh(task)
        return self._task_response(task)

    def list_tasks(self, member_id, task_id, project_id, status_id):
        query = self._db.query(Tasks).join(Projects, Tasks.project_id == Projects.project_id).filter(
            Projects.owner_user_id == member_id,
            Projects.organization_id.is_(None),
            Projects.isDelete == False,
            Tasks.isDelete == False,
        )
        if task_id is not None:
            query = query.filter(Tasks.task_id == task_id)
        if project_id is not None:
            query = query.filter(Tasks.project_id == project_id)
        if status_id is not None:
            query = query.filter(Tasks.status_id == status_id)
        return [self._task_response(task) for task in query.order_by(Tasks.created_at.desc()).all()]

    def delete_task(self, member_id, task_id):
        task = self._task(member_id, task_id)
        task.isDelete = True
        self._db.commit()

    def set_task_status(self, member_id, task_id, status_id):
        task = self._task(member_id, task_id)
        status = self._status(task.project_id, status_id)
        task.status_id = status.status_id
        task.status_name = status.name
        self._db.commit()
        self._db.refresh(task)
        return self._task_response(task)

    def move_task_to_status(self, member_id, task_id, status_id):
        task = self._task(member_id, task_id)
        status = self._status(task.project_id, status_id)
        self._db.add(TaskStatusHistory(task_id=task.task_id, old_status_id=task.status_id,
                                       old_status_name=task.status_name, new_status_id=status.status_id,
                                       new_status_name=status.name, changed_by=member_id))
        task.status_id = status.status_id
        task.status_name = status.name
        self._db.commit()
        self._db.refresh(task)
        return {"task_id": task.task_id, "status_id": task.status_id, "status_name": task.status_name}

    def _personal_project(self, member_id, project_id):
        project = self._db.query(Projects).filter(
            Projects.project_id == project_id,
            Projects.isDelete == False,
        ).first()
        if not project:
            raise WorkspaceNotFound("Project not found")
        if project.organization_id is not None or project.owner_user_id != member_id:
            raise WorkspaceForbidden("Not authorized to access this project")
        return project

    def _task(self, member_id, task_id):
        task = self._db.query(Tasks).join(Projects, Tasks.project_id == Projects.project_id).filter(
            Tasks.task_id == task_id,
            Tasks.isDelete == False,
            Projects.owner_user_id == member_id,
            Projects.organization_id.is_(None),
            Projects.isDelete == False,
        ).first()
        if not task:
            raise WorkspaceNotFound("Task not found")
        return task

    def _status(self, project_id, status_id):
        status = self._db.query(ProjectStatus).filter(
            ProjectStatus.status_id == status_id,
            ProjectStatus.project_id == project_id,
        ).first()
        if not status:
            raise WorkspaceNotFound("Status not found or does not belong to this project")
        return status

    def _task_response(self, task):
        return {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "status_id": task.status_id,
            "status_name": task.status_name,
            "created_by": task.created_by,
            "assigned_to": task.assigned_to,
            "name": task.name,
            "description": task.description,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }
