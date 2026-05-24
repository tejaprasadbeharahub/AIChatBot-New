from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskPrediction(Base):
    """Persists every agricultural risk prediction to Supabase."""

    __tablename__ = "risk_predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Request fields
    crop: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    weather_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)
    soil_condition: Mapped[str | None] = mapped_column(Text, nullable=True)
    disease_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    market_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    pest_signals: Mapped[str | None] = mapped_column(Text, nullable=True)
    irrigation_status: Mapped[str | None] = mapped_column(Text, nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI result fields
    overall_risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    key_risks: Mapped[list] = mapped_column(JSON, nullable=False)
    weather_risk_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    disease_risk_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    market_risk_analysis: Mapped[str] = mapped_column(Text, nullable=False)
    short_term_forecast: Mapped[str] = mapped_column(Text, nullable=False)
    long_term_forecast: Mapped[str] = mapped_column(Text, nullable=False)
    preventive_actions: Mapped[dict] = mapped_column(JSON, nullable=False)
    farmer_alert_message: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
