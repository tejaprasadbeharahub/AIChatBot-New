"""m0n1o2p3q4r5_create_market_intelligence_table

Revision ID: m0n1o2p3q4r5
Revises: l9m0n1o2p3q4
Create Date: 2026-05-23 20:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "m0n1o2p3q4r5"
down_revision: Union[str, None] = "l9m0n1o2p3q4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "market_intelligence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("crop", sa.String(255), nullable=False),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("current_price", sa.String(255), nullable=True),
        sa.Column("quantity", sa.String(255), nullable=True),
        sa.Column("storage_available", sa.String(255), nullable=True),
        sa.Column("weather", sa.String(255), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("current_market_trend", sa.String(20), nullable=False),
        sa.Column("price_outlook", sa.Text(), nullable=False),
        sa.Column("recommended_action", sa.String(20), nullable=False),
        sa.Column("best_selling_window_days", sa.Integer(), nullable=False),
        sa.Column("expected_profit_change_percent", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("farmer_advice", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_intelligence_crop", "market_intelligence", ["crop"])
    op.create_index("ix_market_intelligence_region", "market_intelligence", ["region"])
    op.create_index("ix_market_intelligence_recommended_action", "market_intelligence", ["recommended_action"])
    op.create_index("ix_market_intelligence_risk_level", "market_intelligence", ["risk_level"])
    op.create_index("ix_market_intelligence_created_at", "market_intelligence", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_market_intelligence_created_at", "market_intelligence")
    op.drop_index("ix_market_intelligence_risk_level", "market_intelligence")
    op.drop_index("ix_market_intelligence_recommended_action", "market_intelligence")
    op.drop_index("ix_market_intelligence_region", "market_intelligence")
    op.drop_index("ix_market_intelligence_crop", "market_intelligence")
    op.drop_table("market_intelligence")
