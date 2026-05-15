"""
Research Session model — stores research queries and generated digests.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ResearchSession(Base):
    """Stores a research query session with generated digest."""
    __tablename__ = "research_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )

    research_query: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(default="in_progress", nullable=False)  # in_progress, completed, failed
    papers_found: Mapped[int] = mapped_column(default=0, nullable=False)
    digest_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    digest_full: Mapped[str | None] = mapped_column(Text, nullable=True)  # Full JSON digest
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    chat: Mapped["Chat"] = relationship("Chat", back_populates="research_sessions")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="research_sessions")  # noqa: F821
    message: Mapped["Message"] = relationship("Message", back_populates="research_sessions")  # noqa: F821
    papers: Mapped[list["ResearchPaper"]] = relationship("ResearchPaper", back_populates="session", cascade="all, delete-orphan")


class ResearchPaper(Base):
    """Stores papers found during research."""
    __tablename__ = "research_papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("research_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    arxiv_id: Mapped[str] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array of names
    abstract: Mapped[str] = mapped_column(Text, nullable=False)
    published_date: Mapped[str] = mapped_column(nullable=False)  # ISO format
    categories: Mapped[str] = mapped_column(Text, nullable=False)  # comma-separated
    pdf_url: Mapped[str] = mapped_column(nullable=False)
    relevance_score: Mapped[float] = mapped_column(default=0.0, nullable=False)
    inclusion_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    session: Mapped["ResearchSession"] = relationship("ResearchSession", back_populates="papers")
