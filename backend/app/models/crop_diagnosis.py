from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CropDiagnosis(Base):
    """Persists every Agricultural AI Doctor diagnosis to Supabase."""

    __tablename__ = "crop_diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    crop_type: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    weather: Mapped[str | None] = mapped_column(String(255), nullable=True)
    soil_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI diagnosis result fields
    disease_name: Mapped[str] = mapped_column(String(500), nullable=False)
    scientific_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    urgency_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    affected_parts: Mapped[list] = mapped_column(JSON, nullable=False)
    symptoms_matched: Mapped[list] = mapped_column(JSON, nullable=False)
    likely_causes: Mapped[list] = mapped_column(JSON, nullable=False)
    treatment_steps: Mapped[list] = mapped_column(JSON, nullable=False)
    organic_solutions: Mapped[list] = mapped_column(JSON, nullable=False)
    chemical_solutions: Mapped[list] = mapped_column(JSON, nullable=False)
    preventive_measures: Mapped[list] = mapped_column(JSON, nullable=False)
    best_season_to_act: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
