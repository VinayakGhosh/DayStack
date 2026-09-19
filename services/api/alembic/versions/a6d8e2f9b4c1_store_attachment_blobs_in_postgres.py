"""store Attachment blobs in PostgreSQL

Revision ID: a6d8e2f9b4c1
Revises: e4a1f1a4c2f7
"""

from alembic import op
import sqlalchemy as sa


revision = "a6d8e2f9b4c1"
down_revision = "e4a1f1a4c2f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Retain legacy object-storage metadata so a later production migration can
    # locate existing objects. New Attachment rows use PostgreSQL blobs instead.
    op.alter_column("attachments", "storage_key", existing_type=sa.String(), nullable=True)
    op.alter_column("attachments", "original_filename", new_column_name="filename")
    op.create_table(
        "attachment_blobs",
        sa.Column(
            "attachment_id",
            sa.UUID(),
            sa.ForeignKey("attachments.attachment_id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("content", sa.LargeBinary(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("attachment_blobs")
    op.alter_column("attachments", "filename", new_column_name="original_filename")
