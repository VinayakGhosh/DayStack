import uuid
from db.db import Base
from sqlalchemy import Column, TIMESTAMP, String, UUID, Integer, Boolean, text

class Plans(Base):
    __tablename__ = "plans"

    plan_id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    plan_tier = Column(String, nullable=False)
    price = Column(Integer, nullable=True)
    duration_days = Column(Integer, nullable=True)
    max_projects = Column(Integer, nullable=False)
    task_per_day = Column(Integer, nullable=False)
    export_allowed = Column(Boolean, nullable=False)
    is_discontinued = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    is_deleted = Column(Boolean, nullable=False, server_default=text("false"), default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))