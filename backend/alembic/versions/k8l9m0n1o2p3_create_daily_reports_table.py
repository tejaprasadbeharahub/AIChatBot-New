"""k8l9m0n1o2p3_create_daily_reports_table

Revision ID: k8l9m0n1o2p3
Revises: j7k8l9m0n1o2
Create Date: 2026-05-23 11:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "k8l9m0n1o2p3"
down_revision: Union[str, None] = "j7k8l9m0n1o2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_date", sa.Date(), nullable=False),
        sa.Column("total_requests", sa.Integer(), nullable=False),
        sa.Column("high_priority_count", sa.Integer(), nullable=False),
        sa.Column("medium_priority_count", sa.Integer(), nullable=False),
        sa.Column("low_priority_count", sa.Integer(), nullable=False),
        sa.Column("research_completed_count", sa.Integer(), nullable=False),
        sa.Column("classified_count", sa.Integer(), nullable=False),
        sa.Column("pending_count", sa.Integer(), nullable=False),
        sa.Column("failed_workflows", sa.Integer(), nullable=False),
        sa.Column("retry_attempts", sa.Integer(), nullable=False),
        sa.Column("avg_confidence_score", sa.Float(), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=False),
        sa.Column("key_insights", postgresql.JSON(), nullable=False),
        sa.Column("risks", postgresql.JSON(), nullable=False),
        sa.Column("recommendations", postgresql.JSON(), nullable=False),
        sa.Column("workflow_efficiency_score", sa.Integer(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("report_date"),
    )
    op.create_index("ix_daily_reports_report_date", "daily_reports", ["report_date"], unique=False)
    op.create_index("ix_daily_reports_generated_at", "daily_reports", ["generated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_daily_reports_generated_at", table_name="daily_reports")
    op.drop_index("ix_daily_reports_report_date", table_name="daily_reports")
    op.drop_table("daily_reports")
