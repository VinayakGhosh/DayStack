"""SQLAlchemy adapter for the Task Workspace port.

Only this adapter knows about ORM models.  HTTP handlers work with the
TaskWorkspace application service instead of mutating models directly.
"""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.Project import ProjectStatus, Projects
from models.Task import Labels, Subtasks, TaskLabels, Tasks
from models.Task import TaskStatusHistory
from models.user import Users


class WorkspaceProblem(Exception):
    """A stable member-visible problem returned by Task Workspace."""

    status_code = 409
    code = "conflict"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        if code is not None:
            self.code = code


class WorkspaceNotFound(WorkspaceProblem):
    """The requested member-visible work item does not exist."""

    status_code = 404
    code = "not_found"


class WorkspaceForbidden(WorkspaceProblem):
    """The member does not own the requested work item."""

    status_code = 403
    code = "forbidden"


class WorkspaceConflict(WorkspaceProblem):
    """The requested change conflicts with existing work."""


class WorkspaceProjectLimitReached(WorkspaceConflict):
    """A Member already owns the maximum number of active Projects."""

    code = "project_limit_reached"


class WorkspaceTaskLimitReached(WorkspaceConflict):
    """A Project already has the maximum number of active Tasks."""

    code = "task_limit_reached"


class SqlAlchemyTaskWorkspaceRepository:
    def __init__(self, db: Session):
        self._db = db

    def list_projects(self, member_id):
        done_statuses = (
            select(ProjectStatus.status_id)
            .join(Projects, ProjectStatus.project_id == Projects.project_id)
            .where(
                Projects.owner_user_id == member_id,
                ProjectStatus.is_completion.is_(True),
            )
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
        # Locking the Member row serializes active-Project counting and creation
        # for this Member on PostgreSQL.  A deleted Project no longer consumes quota.
        member = self._db.query(Users).filter(Users.user_id == member_id).with_for_update().first()
        if member is None:
            raise WorkspaceNotFound("Member not found")
        active_projects = self._db.query(Projects).filter(
            Projects.owner_user_id == member_id,
            Projects.organization_id.is_(None),
            Projects.isDelete.is_(False),
        ).count()
        if active_projects >= 5:
            raise WorkspaceProjectLimitReached("You can have up to five Projects.")
        project = Projects(
            owner_user_id=member_id,
            organization_id=None,
            name=name,
            description=description,
        )
        self._db.add(project)
        self._db.flush()
        for status in (
            ("To Do", "Task is not yet started", False, 0),
            ("In Progress", "Task is actively being worked on", False, 1),
            ("Completed", "Task has been completed", True, 2),
        ):
            self._db.add(ProjectStatus(
                project_id=project.project_id,
                name=status[0],
                description=status[1],
                is_completion=status[2],
                display_order=status[3],
            ))
        self._db.commit()
        self._db.refresh(project)
        return project

    def project_quota(self, member_id):
        used = self._db.query(Projects).filter(
            Projects.owner_user_id == member_id,
            Projects.organization_id.is_(None),
            Projects.isDelete.is_(False),
        ).count()
        return {"used": used, "limit": 5, "remaining": 5 - used}

    def get_project(self, member_id, project_id):
        project = self._personal_project(member_id, project_id)
        completion_statuses = select(ProjectStatus.status_id).where(
            ProjectStatus.project_id == project_id,
            ProjectStatus.is_completion.is_(True),
        )
        total_tasks = self._db.query(Tasks).filter(
            Tasks.project_id == project_id,
            Tasks.isDelete.is_(False),
        ).count()
        completed_tasks = self._db.query(Tasks).filter(
            Tasks.project_id == project_id,
            Tasks.isDelete.is_(False),
            Tasks.status_id.in_(completion_statuses),
        ).count()
        return project, total_tasks, completed_tasks

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
        self._db.delete(project)
        self._db.commit()

    def list_statuses(self, member_id, project_id):
        self._personal_project(member_id, project_id)
        return self._db.query(ProjectStatus).filter(
            ProjectStatus.project_id == project_id
        ).order_by(ProjectStatus.display_order, ProjectStatus.created_at).all()

    def create_status(self, member_id, project_id, name, description):
        # The Project lock serializes creation even when there are no existing
        # status rows to lock yet, preserving a deterministic display order.
        self._locked_personal_project(member_id, project_id)
        statuses = self._locked_statuses(project_id)
        last_status = statuses[-1] if statuses else None
        status = ProjectStatus(
            project_id=project_id,
            name=name,
            description=description,
            is_completion=False,
            display_order=(last_status.display_order + 1) if last_status else 0,
        )
        self._db.add(status)
        self._db.commit()
        self._db.refresh(status)
        return status

    def update_status(self, member_id, project_id, status_id, name, description, is_completion=None):
        self._personal_project(member_id, project_id)
        statuses = self._locked_statuses(project_id)
        status = self._status_from(statuses, status_id)
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
        if is_completion is True:
            for candidate in statuses:
                if candidate.status_id != status_id and candidate.is_completion:
                    candidate.is_completion = False
            self._db.flush()
            status.is_completion = True
        elif is_completion is False and status.is_completion:
            if sum(candidate.is_completion for candidate in statuses) == 1:
                raise WorkspaceConflict(
                    "Choose another completion status before unmarking this one.",
                    code="completion_status_required",
                )
            status.is_completion = False
        self._db.commit()
        self._db.refresh(status)
        return status

    def reorder_statuses(self, member_id, project_id, status_ids):
        self._personal_project(member_id, project_id)
        statuses = self._locked_statuses(project_id)
        if len(status_ids) != len(statuses) or set(status_ids) != {status.status_id for status in statuses}:
            raise WorkspaceConflict(
                "The Workflow status order must include every status exactly once.",
                code="invalid_status_order",
            )
        statuses_by_id = {status.status_id: status for status in statuses}
        for display_order, status_id in enumerate(status_ids):
            statuses_by_id[status_id].display_order = display_order
        self._db.commit()
        return self.list_statuses(member_id, project_id)

    def delete_status(self, member_id, project_id, status_id, reassign_to_status_id=None):
        self._personal_project(member_id, project_id)
        statuses = self._locked_statuses(project_id)
        status = self._status_from(statuses, status_id)
        if len(statuses) == 1:
            raise WorkspaceConflict(
                "A Project must keep at least one Workflow status.",
                code="completion_status_required",
            )
        if status.is_completion:
            raise WorkspaceConflict(
                "Choose another completion status before removing this one.",
                code="completion_status_required",
            )
        tasks_using = self._db.query(Tasks).filter(
            Tasks.status_id == status_id,
            Tasks.isDelete == False,
        ).count()
        if tasks_using:
            if reassign_to_status_id is None:
                raise WorkspaceConflict(
                    "Reassign this status's Tasks before removing it.",
                    code="status_in_use",
                )
            if reassign_to_status_id == status_id:
                raise WorkspaceConflict(
                    "Choose a different Workflow status for reassignment.",
                    code="invalid_status_reassignment",
                )
            replacement = self._status_from(statuses, reassign_to_status_id)
            for task in self._db.query(Tasks).filter(
                Tasks.status_id == status_id,
                Tasks.isDelete.is_(False),
            ).all():
                self._db.add(TaskStatusHistory(
                    task_id=task.task_id,
                    old_status_id=status.status_id,
                    old_status_name=status.name,
                    new_status_id=replacement.status_id,
                    new_status_name=replacement.name,
                    changed_by=member_id,
                ))
                task.status_id = replacement.status_id
                task.status_name = replacement.name
        self._db.delete(status)
        for display_order, remaining_status in enumerate(
            sorted((item for item in statuses if item.status_id != status_id), key=lambda item: item.display_order)
        ):
            remaining_status.display_order = display_order
        self._db.commit()

    def create_task(self, member_id, project_id, name, description, due_date=None, priority="none", label_ids=None, subtasks=None):
        self._locked_personal_project(member_id, project_id)
        self._ensure_task_capacity(project_id)
        todo = self._db.query(ProjectStatus).filter(
            ProjectStatus.project_id == project_id,
        ).order_by(ProjectStatus.display_order, ProjectStatus.created_at).first()
        task = Tasks(project_id=project_id, created_by=member_id, assigned_to=None,
                     status_id=todo.status_id if todo else None, status_name=todo.name if todo else None,
                     name=name, description=description, due_date=self._date(due_date), priority=self._priority(priority))
        self._db.add(task)
        self._db.flush()
        self._set_task_labels(member_id, task.task_id, label_ids or [])
        self._replace_subtasks(task.task_id, subtasks or [])
        self._db.add(TaskStatusHistory(task_id=task.task_id, old_status_id=None, old_status_name=None,
                                       new_status_id=todo.status_id if todo else None,
                                       new_status_name=todo.name if todo else None, changed_by=member_id))
        self._db.commit()
        self._db.refresh(task)
        return self._task_response(task)

    def update_task(self, member_id, task_id, name, description, due_date=None, priority=None, label_ids=None, subtasks=None, updated_fields=None):
        task = self._task(member_id, task_id)
        updated_fields = updated_fields or {field for field, value in {
            "name": name, "description": description, "due_date": due_date, "priority": priority,
            "label_ids": label_ids, "subtasks": subtasks,
        }.items() if value is not None}
        if "name" in updated_fields:
            task.name = name
        if "description" in updated_fields:
            task.description = description
        if "due_date" in updated_fields:
            task.due_date = self._date(due_date)
        if "priority" in updated_fields:
            task.priority = self._priority(priority)
        if "label_ids" in updated_fields:
            self._set_task_labels(member_id, task.task_id, label_ids or [])
        if "subtasks" in updated_fields:
            self._replace_subtasks(task.task_id, subtasks or [])
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
        self._db.delete(task)
        self._db.commit()

    def set_task_status(self, member_id, task_id, status_id):
        task = self._locked_task(member_id, task_id)
        status = self._status(task.project_id, status_id)
        self._ensure_status_move_capacity(task, status)
        task.status_id = status.status_id
        task.status_name = status.name
        self._db.commit()
        self._db.refresh(task)
        return self._task_response(task)

    def move_task_to_status(self, member_id, task_id, status_id):
        task = self._locked_task(member_id, task_id)
        status = self._status(task.project_id, status_id)
        self._ensure_status_move_capacity(task, status)
        self._db.add(TaskStatusHistory(task_id=task.task_id, old_status_id=task.status_id,
                                       old_status_name=task.status_name, new_status_id=status.status_id,
                                       new_status_name=status.name, changed_by=member_id))
        task.status_id = status.status_id
        task.status_name = status.name
        self._db.commit()
        self._db.refresh(task)
        return self._task_response(task)

    def task_quota(self, member_id, project_id):
        self._personal_project(member_id, project_id)
        active = self._active_task_count(project_id)
        return {"used": active, "limit": 30, "remaining": 30 - active}

    def list_labels(self, member_id):
        return [self._label_response(label) for label in self._db.query(Labels).filter(
            Labels.member_id == member_id
        ).order_by(Labels.name).all()]

    def create_label(self, member_id, name, color):
        label = self._db.query(Labels).filter(Labels.member_id == member_id, Labels.name == name).first()
        if label is None:
            label = Labels(member_id=member_id, name=name, color=color)
            self._db.add(label)
            self._db.commit()
            self._db.refresh(label)
        return self._label_response(label)

    def update_label(self, member_id, label_id, name, color):
        label = self._label(member_id, label_id)
        if name is not None:
            existing = self._db.query(Labels).filter(
                Labels.member_id == member_id, Labels.name == name, Labels.label_id != label_id
            ).first()
            if existing:
                raise WorkspaceConflict("You already have a Label with this name.", code="label_name_in_use")
            label.name = name
        if color is not None:
            label.color = color
        self._db.commit()
        self._db.refresh(label)
        return self._label_response(label)

    def delete_label(self, member_id, label_id):
        self._db.delete(self._label(member_id, label_id))
        self._db.commit()

    def set_subtasks(self, member_id, task_id, subtasks):
        task = self._task(member_id, task_id)
        self._replace_subtasks(task.task_id, subtasks)
        self._db.commit()
        return self._task_response(task)

    def toggle_subtask(self, member_id, task_id, subtask_id, is_completed):
        self._task(member_id, task_id)
        subtask = self._db.query(Subtasks).filter(
            Subtasks.subtask_id == subtask_id, Subtasks.task_id == task_id
        ).first()
        if subtask is None:
            raise WorkspaceNotFound("Subtask not found")
        subtask.is_completed = is_completed
        self._db.commit()
        return self._subtask_response(subtask)

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

    def _locked_personal_project(self, member_id, project_id):
        project = self._db.query(Projects).filter(
            Projects.project_id == project_id,
            Projects.isDelete.is_(False),
        ).with_for_update().first()
        if not project:
            raise WorkspaceNotFound("Project not found")
        if project.organization_id is not None or project.owner_user_id != member_id:
            raise WorkspaceForbidden("Not authorized to access this Project")
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

    def _locked_task(self, member_id, task_id):
        task = self._task(member_id, task_id)
        self._locked_personal_project(member_id, task.project_id)
        return task

    def _status(self, project_id, status_id):
        status = self._db.query(ProjectStatus).filter(
            ProjectStatus.status_id == status_id,
            ProjectStatus.project_id == project_id,
        ).first()
        if not status:
            raise WorkspaceNotFound("Status not found or does not belong to this project")
        return status

    def _locked_statuses(self, project_id):
        return self._db.query(ProjectStatus).filter(
            ProjectStatus.project_id == project_id,
        ).with_for_update().order_by(ProjectStatus.display_order, ProjectStatus.created_at).all()

    def _status_from(self, statuses, status_id):
        for status in statuses:
            if status.status_id == status_id:
                return status
        raise WorkspaceNotFound("Status not found or does not belong to this Project")

    def _task_response(self, task):
        return {
            "task_id": task.task_id,
            "project_id": task.project_id,
            "status_id": task.status_id,
            "status_name": task.status_name,
            "created_by": task.created_by,
            "name": task.name,
            "description": task.description,
            "due_date": task.due_date,
            "priority": task.priority,
            "labels": [self._label_response(label) for label in self._db.query(Labels).join(
                TaskLabels, Labels.label_id == TaskLabels.label_id
            ).filter(TaskLabels.task_id == task.task_id).order_by(Labels.name).all()],
            "subtasks": [self._subtask_response(subtask) for subtask in self._db.query(Subtasks).filter(
                Subtasks.task_id == task.task_id
            ).order_by(Subtasks.display_order).all()],
            "created_at": task.created_at,
            "updated_at": task.updated_at,
        }

    def _active_task_count(self, project_id):
        completion_statuses = select(ProjectStatus.status_id).where(
            ProjectStatus.project_id == project_id,
            ProjectStatus.is_completion.is_(True),
        )
        return self._db.query(Tasks).filter(
            Tasks.project_id == project_id,
            Tasks.isDelete.is_(False),
            ~Tasks.status_id.in_(completion_statuses),
        ).count()

    def _ensure_task_capacity(self, project_id):
        if self._active_task_count(project_id) >= 30:
            raise WorkspaceTaskLimitReached("A Project can have up to thirty active Tasks.")

    def _ensure_status_move_capacity(self, task, status):
        current = self._status(task.project_id, task.status_id) if task.status_id else None
        if current is not None and current.is_completion and not status.is_completion:
            self._ensure_task_capacity(task.project_id)

    def _set_task_labels(self, member_id, task_id, label_ids):
        if len(label_ids) != len(set(label_ids)):
            raise WorkspaceConflict("A Label can only be applied once.", code="duplicate_label")
        labels = [self._label(member_id, label_id) for label_id in label_ids]
        self._db.query(TaskLabels).filter(TaskLabels.task_id == task_id).delete()
        for label in labels:
            self._db.add(TaskLabels(task_id=task_id, label_id=label.label_id))

    def _replace_subtasks(self, task_id, subtasks):
        self._db.query(Subtasks).filter(Subtasks.task_id == task_id).delete()
        for display_order, item in enumerate(subtasks):
            text_value = item.get("text", "").strip()
            if not text_value:
                raise WorkspaceConflict("A Subtask needs text.", code="invalid_subtask")
            self._db.add(Subtasks(
                task_id=task_id,
                text=text_value,
                display_order=display_order,
                is_completed=bool(item.get("is_completed", False)),
            ))

    def _label(self, member_id, label_id):
        label = self._db.query(Labels).filter(Labels.label_id == label_id).first()
        if label is None:
            raise WorkspaceNotFound("Label not found")
        if label.member_id != member_id:
            raise WorkspaceForbidden("Not authorized to access this Label")
        return label

    def _label_response(self, label):
        return {"label_id": label.label_id, "name": label.name, "color": label.color}

    def _subtask_response(self, subtask):
        return {
            "subtask_id": subtask.subtask_id,
            "text": subtask.text,
            "display_order": subtask.display_order,
            "is_completed": subtask.is_completed,
        }

    def _priority(self, priority):
        normalized = priority.lower()
        if normalized not in {"none", "low", "medium", "high"}:
            raise WorkspaceConflict("Priority must be None, Low, Medium, or High.", code="invalid_priority")
        return normalized

    def _date(self, due_date):
        if due_date is None or isinstance(due_date, date):
            return due_date
        try:
            return date.fromisoformat(due_date)
        except ValueError as error:
            raise WorkspaceConflict("Due date must be a calendar date.", code="invalid_due_date") from error
