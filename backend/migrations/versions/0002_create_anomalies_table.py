"""create anomalies table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-19

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "anomalies",
        sa.Column("id",             sa.String(36),  primary_key=True),
        sa.Column("source_dataset", sa.String(20),  nullable=False),
        sa.Column("record_id",      sa.String(100), nullable=False),
        sa.Column("anomaly_type",   sa.String(50),  nullable=False),
        sa.Column("severity",       sa.String(20),  nullable=False),
        sa.Column("status",         sa.String(20),  nullable=False, server_default="OPEN"),
        sa.Column("affected_field", sa.String(255), nullable=False),
        sa.Column("error_message",  sa.Text,        nullable=False),
        sa.Column("likely_cause",   sa.Text,        nullable=True),
        sa.Column("recommended_fix",sa.Text,        nullable=True),
        sa.Column("raw_record",     postgresql.JSONB, nullable=True),
        sa.Column("timestamp",      sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at",     sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("assigned_to",    sa.String(36),  nullable=True),
    )
    op.create_index("ix_anomalies_id",        "anomalies", ["id"])
    op.create_index("ix_anomalies_record_id", "anomalies", ["record_id"])
    op.create_index("ix_anomalies_severity",  "anomalies", ["severity"])
    op.create_index("ix_anomalies_status",    "anomalies", ["status"])
    op.create_index("ix_anomalies_timestamp", "anomalies", ["timestamp"])


def downgrade() -> None:
    op.drop_index("ix_anomalies_timestamp", table_name="anomalies")
    op.drop_index("ix_anomalies_status",    table_name="anomalies")
    op.drop_index("ix_anomalies_severity",  table_name="anomalies")
    op.drop_index("ix_anomalies_record_id", table_name="anomalies")
    op.drop_index("ix_anomalies_id",        table_name="anomalies")
    op.drop_table("anomalies")
