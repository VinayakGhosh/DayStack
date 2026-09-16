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
    op.execute("UPDATE project_statuses SET is_completion = true WHERE lower(name) = 'done'")


def downgrade() -> None:
    op.drop_column("project_statuses", "is_completion")
