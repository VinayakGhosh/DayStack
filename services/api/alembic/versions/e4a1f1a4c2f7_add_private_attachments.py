"""add private Task attachment metadata and cleanup jobs

Revision ID: e4a1f1a4c2f7
Revises: d6dce0c27972
"""

from alembic import op
import sqlalchemy as sa


revision = "e4a1f1a4c2f7"
down_revision = "d6dce0c27972"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attachments",
        sa.Column("attachment_id", sa.UUID(), primary_key=True),
        sa.Column("task_id", sa.UUID(), sa.ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("media_type", sa.String(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False, unique=True),
        sa.Column("upload_state", sa.String(), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_attachments_task_id", "attachments", ["task_id"])
    op.create_table(
        "attachment_cleanup_jobs",
        sa.Column("cleanup_id", sa.UUID(), primary_key=True),
        sa.Column("storage_key", sa.String(), nullable=False, unique=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("attachment_cleanup_jobs")
    op.drop_index("ix_attachments_task_id", table_name="attachments")
    op.drop_table("attachments")
