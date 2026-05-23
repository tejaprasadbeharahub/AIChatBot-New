from __future__ import annotations

import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_workflow_db
from app.schemas.daily_summary import DailySummaryRequest, DailySummaryResponse
from app.services.workflow.analytics_service import (
    AnalyticsAgentError,
    AnalyticsAgentService,
)


router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/daily-summary", response_model=DailySummaryResponse)
async def daily_summary(
    payload: DailySummaryRequest,
    db: Session = Depends(get_workflow_db),
) -> DailySummaryResponse:
    """
    Generate AI-powered daily analytics summary from workflow activity.
    
    This endpoint is triggered by N8N Cron workflow daily at 9 AM.
    
    Process:
    1. Validates input date (YYYY-MM-DD, not future)
    2. Aggregates workflow metrics from PostgreSQL
    3. Analyzes daily trends via LiteLLM
    4. Generates operational insights and recommendations
    5. Persists report to daily_reports table
    6. Returns structured analytics response
    """
    service = AnalyticsAgentService(db)
    report_date = date.fromisoformat(payload.date)

    try:
        metrics, analytics = await service.generate_daily_summary(report_date)
    except AnalyticsAgentError as exc:
        logger.warning("analytics_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("daily_summary_unhandled_error")
        raise HTTPException(status_code=500, detail="Daily summary generation failed") from exc

    return DailySummaryResponse(
        success=True,
        report_date=payload.date,
        metrics={
            "total_requests": metrics["total_requests"],
            "high_priority_count": metrics["high_priority_count"],
            "medium_priority_count": metrics["medium_priority_count"],
            "low_priority_count": metrics["low_priority_count"],
            "research_completed_count": metrics["research_completed_count"],
            "classified_count": metrics["classified_count"],
            "pending_count": metrics["pending_count"],
            "failed_workflows": metrics["failed_workflows"],
            "retry_attempts": metrics["retry_attempts"],
            "avg_confidence_score": metrics["avg_confidence_score"],
        },
        ai_report={
            "executive_summary": analytics.executive_summary,
            "key_insights": analytics.key_insights,
            "risks": analytics.risks,
            "recommendations": analytics.recommendations,
            "workflow_efficiency_score": analytics.workflow_efficiency_score,
        },
    )
