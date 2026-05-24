"""n1o2p3q4r5s6_create_risk_predictions_table

Revision ID: n1o2p3q4r5s6
Revises: m0n1o2p3q4r5
Create Date: 2026-05-23 21:10:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "n1o2p3q4r5s6"
down_revision: Union[str, None] = "m0n1o2p3q4r5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crop", sa.String(255), nullable=False),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("weather_conditions", sa.Text(), nullable=True),
        sa.Column("soil_condition", sa.Text(), nullable=True),
        sa.Column("disease_signals", sa.Text(), nullable=True),
        sa.Column("market_signals", sa.Text(), nullable=True),
        sa.Column("pest_signals", sa.Text(), nullable=True),
        sa.Column("irrigation_status", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("overall_risk_level", sa.String(20), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("key_risks", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("weather_risk_analysis", sa.Text(), nullable=False),
        sa.Column("disease_risk_analysis", sa.Text(), nullable=False),
        sa.Column("market_risk_analysis", sa.Text(), nullable=False),
        sa.Column("short_term_forecast", sa.Text(), nullable=False),
        sa.Column("long_term_forecast", sa.Text(), nullable=False),
        sa.Column("preventive_actions", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("farmer_alert_message", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_risk_predictions_crop", "risk_predictions", ["crop"])
    op.create_index("ix_risk_predictions_location", "risk_predictions", ["location"])
    op.create_index("ix_risk_predictions_overall_risk_level", "risk_predictions", ["overall_risk_level"])
    op.create_index("ix_risk_predictions_created_at", "risk_predictions", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_risk_predictions_created_at", "risk_predictions")
    op.drop_index("ix_risk_predictions_overall_risk_level", "risk_predictions")
    op.drop_index("ix_risk_predictions_location", "risk_predictions")
    op.drop_index("ix_risk_predictions_crop", "risk_predictions")
    op.drop_table("risk_predictions")
