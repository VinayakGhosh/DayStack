"""enforce project workflow invariants

Revision ID: f15e3d4c2b91
Revises: e47f6b812c02
"""

from alembic import op
import sqlalchemy as sa


revision = "f15e3d4c2b91"
down_revision = "e47f6b812c02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Preserve one existing completion status per Project, or choose its last
    # status for legacy Projects whose statuses predate the completion flag.
    op.execute("""
        WITH selected_completion AS (
            SELECT DISTINCT ON (project_id) project_id, status_id
            FROM project_statuses
            ORDER BY project_id, is_completion DESC, display_order DESC, created_at DESC
        )
        UPDATE project_statuses AS status
        SET is_completion = (status.status_id = selected_completion.status_id)
        FROM selected_completion
        WHERE status.project_id = selected_completion.project_id
    """)
    op.create_index(
        "ix_project_statuses_project_display_order",
        "project_statuses",
        ["project_id", "display_order"],
    )
    op.create_index(
        "uq_project_statuses_one_completion",
        "project_statuses",
        ["project_id"],
        unique=True,
        postgresql_where=sa.text("is_completion = true"),
    )


def downgrade() -> None:
    op.drop_index("uq_project_statuses_one_completion", table_name="project_statuses")
    op.drop_index("ix_project_statuses_project_display_order", table_name="project_statuses")
