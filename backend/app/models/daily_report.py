from __future__ import annotations

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DailyReport(Base):
    """Stores daily analytics and workflow metrics summaries."""

    __tablename__ = "daily_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    total_requests: Mapped[int] = mapped_column(Integer, nullable=False)
    high_priority_count: Mapped[int] = mapped_column(Integer, nullable=False)
    medium_priority_count: Mapped[int] = mapped_column(Integer, nullable=False)
    low_priority_count: Mapped[int] = mapped_column(Integer, nullable=False)
    research_completed_count: Mapped[int] = mapped_column(Integer, nullable=False)
    classified_count: Mapped[int] = mapped_column(Integer, nullable=False)
    pending_count: Mapped[int] = mapped_column(Integer, nullable=False)
    failed_workflows: Mapped[int] = mapped_column(Integer, nullable=False)
    retry_attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_insights: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    risks: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    recommendations: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    workflow_efficiency_score: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
