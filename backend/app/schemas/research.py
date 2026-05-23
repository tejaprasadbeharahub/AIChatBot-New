from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ResearchAgentRequest(BaseModel):
    """Request payload for research agent analysis."""

    request_id: UUID = Field(..., description="UUID of the workflow request")
    message: str = Field(..., min_length=10, description="Research task description")

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> str:
        if value is None:
            raise ValueError("message is required")
        if not isinstance(value, str):
            raise ValueError("message must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("message is required")
        if len(normalized) < 10:
            raise ValueError("message must be at least 10 characters")
        return normalized


class ResearchAnalysisResult(BaseModel):
    """AI-generated research analysis output."""

    summary: str = Field(..., description="Comprehensive summary of research findings")
    key_points: list[str] = Field(..., description="Key findings and technologies")
    recommendations: list[str] = Field(..., description="Recommended actions or approaches")
    risks: list[str] = Field(..., description="Identified challenges and risks")
    next_steps: list[str] = Field(..., description="Actionable next steps")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence in analysis quality")


class ResearchAgentResponse(BaseModel):
    """API response with research analysis results."""

    success: bool = Field(..., description="Operation success status")
    request_id: UUID = Field(..., description="UUID of the research request")
    workflow_status: str = Field(..., description="Updated workflow status")
    research_result: ResearchAnalysisResult = Field(
        ..., description="Structured research analysis"
    )
