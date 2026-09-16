import uuid
from sqlalchemy import Column, Integer, String, UUID, Boolean, ForeignKey, TIMESTAMP, text, Date, UniqueConstraint
from db.db import Base

class Organization(Base):
    __tablename__ = "organizations"

    organization_id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

class OrganizationMember(Base):
    __tablename__ = "organization_members"

    organization_member_id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    role = Column(String, nullable=False, default="member")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP"))

class OrganizationInvitation(Base):
    __tablename__ = "organization_invitations"

    invite_id = Column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.organization_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    role = Column(String, nullable=False, default="member")
    status = Column(String, nullable=False, default="pending")
    created_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP"))
    expired_at = Column(TIMESTAMP, server_default=text("CURRENT_TIMESTAMP + INTERVAL '7 days'"))