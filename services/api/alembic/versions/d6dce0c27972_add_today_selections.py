"""add member-local Today selections

Revision ID: d6dce0c27972
Revises: a62f81d4e903
"""

from alembic import op
import sqlalchemy as sa


revision = "d6dce0c27972"
down_revision = "a62f81d4e903"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "today_selections",
        sa.Column("selection_id", sa.UUID(), primary_key=True),
        sa.Column("member_id", sa.UUID(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("local_date", sa.Date(), nullable=False),
        sa.Column("task_id", sa.UUID(), sa.ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("member_id", "local_date", "task_id", name="uq_today_selections_member_date_task"),
        sa.UniqueConstraint("member_id", "local_date", "display_order", name="uq_today_selections_member_date_order"),
    )
    op.create_index("ix_today_selections_member_date", "today_selections", ["member_id", "local_date"])


def downgrade() -> None:
    op.drop_index("ix_today_selections_member_date", table_name="today_selections")
    op.drop_table("today_selections")
