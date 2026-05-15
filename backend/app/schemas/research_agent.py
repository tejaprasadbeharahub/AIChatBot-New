"""
Schemas for Research Digest Agent.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResearchPaperRef(BaseModel):
    """Reference to a research paper."""
    arxiv_id: str
    title: str
    authors: list[str]
    abstract: str
    published_date: str
    categories: list[str]
    pdf_url: str
    relevance_score: float
    inclusion_reason: str | None = None

    model_config = {"from_attributes": True}


class ResearchDigestKeyFinding(BaseModel):
    """A key finding extracted from research."""
    topic: str
    finding: str
    evidence_papers: list[str]  # arxiv_ids


class ResearchDigestMethodology(BaseModel):
    """Common methodologies found in research."""
    name: str
    frequency: int
    papers: list[str]  # arxiv_ids


class ResearchDigestTrend(BaseModel):
    """Research trends identified."""
    trend: str
    direction: str  # increasing, decreasing, stable
    recent_papers: list[str]  # arxiv_ids


class ResearchDigestFull(BaseModel):
    """Full structured research digest."""
    summary: str
    key_findings: list[ResearchDigestKeyFinding]
    methodologies: list[ResearchDigestMethodology]
    limitations: list[str]
    trends: list[ResearchDigestTrend]
    total_papers_reviewed: int
    papers_cited: list[ResearchPaperRef]
    search_duration_seconds: int


class ResearchSessionRead(BaseModel):
    """Read model for research session."""
    id: uuid.UUID
    chat_id: uuid.UUID
    user_id: uuid.UUID
    research_query: str
    status: str
    papers_found: int
    digest_summary: str | None = None
    digest_full: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResearchQueryRequest(BaseModel):
    """Request to start research on a topic."""
    chat_id: uuid.UUID | None = None
    query: str = Field(min_length=5, max_length=2000)
    max_papers: int = Field(default=10, ge=1, le=50)
    depth: str = Field(default="balanced", pattern="^(quick|balanced|deep)$")  # quick, balanced, deep


class ResearchDigestStreamEvent(BaseModel):
    """Event streamed during research."""
    event_type: str  # searching, found_paper, analyzing, generating_digest, completed, error
    data: dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResearchDigestResponse(BaseModel):
    """Final research digest response."""
    session_id: uuid.UUID
    chat_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    query: str
    digest: ResearchDigestFull
    search_duration_seconds: int
    papers_found: int
