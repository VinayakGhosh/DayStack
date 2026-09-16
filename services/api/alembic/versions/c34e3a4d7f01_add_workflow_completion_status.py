"""add workflow completion status

Revision ID: c34e3a4d7f01
Revises: b48b7585cb97
"""

from alembic import op
import sqlalchemy as sa


revision = "c34e3a4d7f01"
down_revision = "b48b7585cb97"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "project_statuses",
        sa.Column("is_completion", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "project_statuses",
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
    )
    op.execute("UPDATE project_statuses SET is_completion = true WHERE lower(name) = 'done'")
    op.execute("""
        UPDATE project_statuses
        SET display_order = CASE lower(name)
            WHEN 'todo' THEN 0
            WHEN 'to do' THEN 0
            WHEN 'in progress' THEN 1
            WHEN 'done' THEN 2
            WHEN 'completed' THEN 2
            ELSE 0
        END
    """)


def downgrade() -> None:
    op.drop_column("project_statuses", "display_order")
    op.drop_column("project_statuses", "is_completion")
