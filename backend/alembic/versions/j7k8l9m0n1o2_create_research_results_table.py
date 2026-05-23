"""j7k8l9m0n1o2_create_research_results_table

Revision ID: j7k8l9m0n1o2
Revises: i2j3k4l5m6n7
Create Date: 2026-05-23 10:15:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "j7k8l9m0n1o2"
down_revision: Union[str, None] = "i2j3k4l5m6n7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("key_points", postgresql.JSON(), nullable=False),
        sa.Column("recommendations", postgresql.JSON(), nullable=False),
        sa.Column("risks", postgresql.JSON(), nullable=False),
        sa.Column("next_steps", postgresql.JSON(), nullable=False),
        sa.Column("confidence_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["request_id"], ["workflow_requests.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_research_results_request_id", "research_results", ["request_id"], unique=False)
    op.create_index("ix_research_results_created_at", "research_results", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_research_results_created_at", table_name="research_results")
    op.drop_index("ix_research_results_request_id", table_name="research_results")
    op.drop_table("research_results")
