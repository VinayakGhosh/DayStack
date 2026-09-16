import uuid
from sqlalchemy import Column, Integer, String, UUID, Boolean, ForeignKey, TIMESTAMP, text, Date, UniqueConstraint
from db.db import Base
from schema.user import UserRoleEnum


class Users(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, server_default=UserRoleEnum.GENERAL.value, default=UserRoleEnum.GENERAL.value)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))


class Subscriptions(Base):
    __tablename__ = "subscriptions"
    subscription_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False,)
    plan_id = Column(UUID, ForeignKey("plans.plan_id"), nullable=False)
    start_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    end_timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))
    

class Usage(Base):
    __tablename__="usage"
    usage_id = Column(UUID(as_uuid=True),primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    feature_name=Column(String, nullable=False)
    feature_count=Column(Integer, nullable=False, default=1)
    date=Column(Date, server_default=text("CURRENT_DATE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=text('now()'), server_default=text('now()'))

    __table_args__ = (
        UniqueConstraint("user_id", "feature_name", "date"),
    )