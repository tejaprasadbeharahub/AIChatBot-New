"""l9m0n1o2p3q4_create_crop_diagnoses_table

Revision ID: l9m0n1o2p3q4
Revises: k8l9m0n1o2p3
Create Date: 2026-05-23 18:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "l9m0n1o2p3q4"
down_revision: Union[str, None] = "k8l9m0n1o2p3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crop_diagnoses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("crop_type", sa.String(255), nullable=True),
        sa.Column("region", sa.String(255), nullable=True),
        sa.Column("weather", sa.String(255), nullable=True),
        sa.Column("soil_type", sa.String(255), nullable=True),
        sa.Column("symptoms", sa.Text(), nullable=True),
        sa.Column("disease_name", sa.String(500), nullable=False),
        sa.Column("scientific_name", sa.String(500), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("urgency_level", sa.String(50), nullable=False),
        sa.Column("affected_parts", postgresql.JSON(), nullable=False),
        sa.Column("symptoms_matched", postgresql.JSON(), nullable=False),
        sa.Column("likely_causes", postgresql.JSON(), nullable=False),
        sa.Column("treatment_steps", postgresql.JSON(), nullable=False),
        sa.Column("organic_solutions", postgresql.JSON(), nullable=False),
        sa.Column("chemical_solutions", postgresql.JSON(), nullable=False),
        sa.Column("preventive_measures", postgresql.JSON(), nullable=False),
        sa.Column("best_season_to_act", sa.Text(), nullable=True),
        sa.Column("additional_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_crop_diagnoses_crop_type", "crop_diagnoses", ["crop_type"])
    op.create_index("ix_crop_diagnoses_region", "crop_diagnoses", ["region"])
    op.create_index("ix_crop_diagnoses_urgency_level", "crop_diagnoses", ["urgency_level"])
    op.create_index("ix_crop_diagnoses_created_at", "crop_diagnoses", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_crop_diagnoses_created_at", table_name="crop_diagnoses")
    op.drop_index("ix_crop_diagnoses_urgency_level", table_name="crop_diagnoses")
    op.drop_index("ix_crop_diagnoses_region", table_name="crop_diagnoses")
    op.drop_index("ix_crop_diagnoses_crop_type", table_name="crop_diagnoses")
    op.drop_table("crop_diagnoses")
