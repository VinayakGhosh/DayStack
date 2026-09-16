import uuid
from db.db import Base
from sqlalchemy import Column, TIMESTAMP, String, UUID, Boolean, text, ForeignKey


class Tasks(Base):
    __tablename__ = "tasks"
    task_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    status_id = Column(UUID, ForeignKey("project_statuses.status_id", ondelete="SET NULL"), nullable=True)
    status_name = Column(String, nullable=True)
    created_by = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    assigned_to = Column(UUID, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True, default="No description")
    isDelete = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    old_status_id = Column(UUID, ForeignKey("project_statuses.status_id", ondelete="SET NULL"), nullable=True)
    old_status_name = Column(String, nullable=True)
    new_status_id = Column(UUID, ForeignKey("project_statuses.status_id", ondelete="SET NULL"), nullable=True)
    new_status_name = Column(String, nullable=True)
    changed_by = Column(UUID, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))


class TaskComment(Base):
    __tablename__ = "task_comments"
    comment_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    description_text = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))
