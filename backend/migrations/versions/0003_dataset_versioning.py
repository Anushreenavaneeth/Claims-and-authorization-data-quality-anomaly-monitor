"""Add dataset_versions table for upload history and versioning.

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-22
"""

from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "dataset_versions",
        sa.Column("id",           sa.String(36),  nullable=False, primary_key=True),
        sa.Column("dataset_type", sa.String(20),  nullable=False),   # CLAIMS / AUTHORIZATION / PHARMACY
        sa.Column("version",      sa.Integer(),   nullable=False, default=1),
        sa.Column("upload_time",  sa.DateTime(timezone=True), nullable=False),
        sa.Column("filename",     sa.String(255), nullable=True),
        sa.Column("source_file",  sa.Text(),      nullable=True),
        sa.Column("record_count", sa.Integer(),   nullable=True),
        sa.Column("valid_count",  sa.Integer(),   nullable=True),
        sa.Column("anomaly_count",sa.Integer(),   nullable=True),
        sa.Column("status",       sa.String(20),  nullable=False, default="pending"),  # pending/processing/complete/failed
        sa.Column("is_current",   sa.Boolean(),   nullable=False, default=False),
        sa.Column("uploaded_by",  sa.String(36),  nullable=True),   # FK to users.id
        sa.Column("notes",        sa.Text(),      nullable=True),
    )
    op.create_index("ix_dataset_versions_dataset_type", "dataset_versions", ["dataset_type"])
    op.create_index("ix_dataset_versions_is_current",   "dataset_versions", ["is_current"])


def downgrade() -> None:
    op.drop_index("ix_dataset_versions_is_current",   table_name="dataset_versions")
    op.drop_index("ix_dataset_versions_dataset_type", table_name="dataset_versions")
    op.drop_table("dataset_versions")
