"""add Task details, Labels, and Subtasks

Revision ID: a62f81d4e903
Revises: f15e3d4c2b91
"""

from alembic import op
import sqlalchemy as sa


revision = "a62f81d4e903"
down_revision = "f15e3d4c2b91"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("due_date", sa.Date(), nullable=True))
    op.add_column("tasks", sa.Column("priority", sa.String(), nullable=False, server_default="none"))
    op.create_table(
        "labels",
        sa.Column("label_id", sa.UUID(), primary_key=True),
        sa.Column("member_id", sa.UUID(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("color", sa.String(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("member_id", "name", name="uq_labels_member_name"),
    )
    op.create_index("ix_labels_member_id", "labels", ["member_id"])
    op.create_table(
        "task_labels",
        sa.Column("task_id", sa.UUID(), sa.ForeignKey("tasks.task_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("label_id", sa.UUID(), sa.ForeignKey("labels.label_id", ondelete="CASCADE"), primary_key=True),
        sa.UniqueConstraint("task_id", "label_id", name="uq_task_labels_task_label"),
    )
    op.create_table(
        "subtasks",
        sa.Column("subtask_id", sa.UUID(), primary_key=True),
        sa.Column("task_id", sa.UUID(), sa.ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.String(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("is_completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_subtasks_task_id", "subtasks", ["task_id"])


def downgrade() -> None:
    op.drop_index("ix_subtasks_task_id", table_name="subtasks")
    op.drop_table("subtasks")
    op.drop_table("task_labels")
    op.drop_index("ix_labels_member_id", table_name="labels")
    op.drop_table("labels")
    op.drop_column("tasks", "priority")
    op.drop_column("tasks", "due_date")
