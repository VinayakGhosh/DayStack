"""SQLAlchemy adapter for the Task Workspace port.

Only this adapter knows about ORM models.  HTTP handlers work with the
TaskWorkspace application service instead of mutating models directly.
"""

from sqlalchemy import func
from sqlalchemy.orm import Session

from models.Project import ProjectStatus, Projects
from models.Task import Tasks


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
