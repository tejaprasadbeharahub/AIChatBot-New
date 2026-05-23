from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator


class DailySummaryRequest(BaseModel):
    """Request payload for daily analytics summary."""

    date: str = Field(..., description="Report date in YYYY-MM-DD format")

    @field_validator("date", mode="before")
    @classmethod
    def validate_date_format(cls, value: object) -> str:
        if value is None:
            raise ValueError("date is required")
        if not isinstance(value, str):
            raise ValueError("date must be a string")
        
        date_str = value.strip()
        if not date_str:
            raise ValueError("date is required")
        
        # Validate format YYYY-MM-DD
        try:
            parsed_date = date.fromisoformat(date_str)
        except ValueError:
            raise ValueError("date must be in YYYY-MM-DD format")
        
        # Reject future dates
        if parsed_date > date.today():
            raise ValueError("date cannot be in the future")
        
        return date_str


class WorkflowMetrics(BaseModel):
    """Aggregated workflow metrics."""

    total_requests: int
    high_priority_count: int
    medium_priority_count: int
    low_priority_count: int
    research_completed_count: int
    classified_count: int
    pending_count: int
    failed_workflows: int
    retry_attempts: int
    avg_confidence_score: float | None


class AnalyticsReport(BaseModel):
    """AI-generated analytics report."""

    executive_summary: str
    key_insights: list[str]
    risks: list[str]
    recommendations: list[str]
    workflow_efficiency_score: int = Field(..., ge=0, le=100)


class DailySummaryResponse(BaseModel):
    """API response with daily analytics."""

    success: bool
    report_date: str
    metrics: WorkflowMetrics
    ai_report: AnalyticsReport
