"""add member sessions and time zone

Revision ID: e47f6b812c02
Revises: c34e3a4d7f01
"""

from alembic import op
import sqlalchemy as sa


revision = "e47f6b812c02"
down_revision = "c34e3a4d7f01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("time_zone", sa.String(), nullable=False, server_default="UTC"))
    op.create_table(
        "member_sessions",
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("refresh_token_hash", sa.String(), nullable=False),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("replaced_by_session_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["replaced_by_session_id"], ["member_sessions.session_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
        sa.UniqueConstraint("refresh_token_hash"),
    )
    op.create_index("ix_member_sessions_user_id", "member_sessions", ["user_id"])
    op.create_index("ix_member_sessions_refresh_token_hash", "member_sessions", ["refresh_token_hash"])


def downgrade() -> None:
    op.drop_index("ix_member_sessions_refresh_token_hash", table_name="member_sessions")
    op.drop_index("ix_member_sessions_user_id", table_name="member_sessions")
    op.drop_table("member_sessions")
    op.drop_column("users", "time_zone")
