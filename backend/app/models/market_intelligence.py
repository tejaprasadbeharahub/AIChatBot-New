from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MarketIntelligence(Base):
    """Persists every Agricultural Market Intelligence query to Supabase."""

    __tablename__ = "market_intelligence"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Request fields
    crop: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    current_price: Mapped[str | None] = mapped_column(String(255), nullable=True)
    quantity: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_available: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weather: Mapped[str | None] = mapped_column(String(255), nullable=True)
    context: Mapped[str | None] = mapped_column(Text, nullable=True)

    # AI result fields
    current_market_trend: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    price_outlook: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    best_selling_window_days: Mapped[int] = mapped_column(Integer, nullable=False)
    expected_profit_change_percent: Mapped[float] = mapped_column(Float, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    farmer_advice: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
