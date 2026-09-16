import uuid
from db.db import Base
from sqlalchemy import Column, TIMESTAMP, String, UUID, Boolean, text, ForeignKey


class Projects(Base):
    __tablename__ = "projects"
    project_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    owner_user_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=True)
    organization_id = Column(UUID, ForeignKey("organizations.organization_id", ondelete="CASCADE"), nullable=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True, default="No description")
    isDelete = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))


class ProjectStatus(Base):
    __tablename__ = "project_statuses"
    status_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    project_id = Column(UUID, ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))
