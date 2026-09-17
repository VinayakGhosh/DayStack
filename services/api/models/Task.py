import uuid
from db.db import Base
from sqlalchemy import Column, TIMESTAMP, String, UUID, Boolean, Date, Integer, text as sql_text, ForeignKey, UniqueConstraint


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
    due_date = Column(Date, nullable=True)
    priority = Column(String, nullable=False, server_default=sql_text("'none'"), default="none")
    isDelete = Column(Boolean, nullable=False, server_default=sql_text("false"), default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=sql_text('now()'), server_default=sql_text('now()'))


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    old_status_id = Column(UUID, ForeignKey("project_statuses.status_id", ondelete="SET NULL"), nullable=True)
    old_status_name = Column(String, nullable=True)
    new_status_id = Column(UUID, ForeignKey("project_statuses.status_id", ondelete="SET NULL"), nullable=True)
    new_status_name = Column(String, nullable=True)
    changed_by = Column(UUID, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))


class TaskComment(Base):
    __tablename__ = "task_comments"
    comment_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    description_text = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=sql_text('now()'), server_default=sql_text('now()'))


class Labels(Base):
    __tablename__ = "labels"
    __table_args__ = (UniqueConstraint("member_id", "name", name="uq_labels_member_name"),)

    label_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    member_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=sql_text('now()'), server_default=sql_text('now()'))


class TaskLabels(Base):
    __tablename__ = "task_labels"
    __table_args__ = (UniqueConstraint("task_id", "label_id", name="uq_task_labels_task_label"),)

    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), primary_key=True)
    label_id = Column(UUID, ForeignKey("labels.label_id", ondelete="CASCADE"), primary_key=True)


class Subtasks(Base):
    __tablename__ = "subtasks"

    subtask_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(String, nullable=False)
    display_order = Column(Integer, nullable=False)
    is_completed = Column(Boolean, nullable=False, server_default="false", default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=sql_text('now()'), server_default=sql_text('now()'))


class TodaySelections(Base):
    __tablename__ = "today_selections"
    __table_args__ = (
        UniqueConstraint("member_id", "local_date", "task_id", name="uq_today_selections_member_date_task"),
        UniqueConstraint("member_id", "local_date", "display_order", name="uq_today_selections_member_date_order"),
    )

    selection_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    member_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    local_date = Column(Date, nullable=False, index=True)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    display_order = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))


class Attachments(Base):
    __tablename__ = "attachments"

    attachment_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    task_id = Column(UUID, ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    byte_size = Column(Integer, nullable=False)
    storage_key = Column(String, nullable=False, unique=True)
    upload_state = Column(String, nullable=False, server_default=sql_text("'pending'"), default="pending")
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=sql_text('now()'), server_default=sql_text('now()'))


class AttachmentCleanupJobs(Base):
    __tablename__ = "attachment_cleanup_jobs"

    cleanup_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    storage_key = Column(String, nullable=False, unique=True)
    attempts = Column(Integer, nullable=False, server_default=sql_text("0"), default=0)
    created_at = Column(TIMESTAMP(timezone=True), server_default=sql_text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=sql_text('now()'), server_default=sql_text('now()'))
