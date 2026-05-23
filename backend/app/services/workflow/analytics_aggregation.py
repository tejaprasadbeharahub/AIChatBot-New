from __future__ import annotations

import logging
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.workflow_request import WorkflowRequest
from app.models.research_result import ResearchResult

logger = logging.getLogger(__name__)


class AnalyticsAggregationService:
    """Aggregates workflow metrics from PostgreSQL."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def aggregate_daily_metrics(self, report_date: date) -> dict:
        """Aggregate all workflow metrics for a given date."""
        # Parse date to get start and end of day
        start_of_day = datetime.combine(report_date, datetime.min.time())
        end_of_day = datetime.combine(report_date, datetime.max.time())

        # Total requests created on this date
        total_requests_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        total_requests = self._db.execute(total_requests_stmt).scalar() or 0

        # Priority distribution
        high_priority_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.priority == "HIGH",
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        high_priority_count = self._db.execute(high_priority_stmt).scalar() or 0

        medium_priority_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.priority == "MEDIUM",
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        medium_priority_count = self._db.execute(medium_priority_stmt).scalar() or 0

        low_priority_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.priority == "LOW",
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        low_priority_count = self._db.execute(low_priority_stmt).scalar() or 0

        # Status distribution
        research_completed_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.workflow_status == "RESEARCH_COMPLETED",
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        research_completed_count = self._db.execute(research_completed_stmt).scalar() or 0

        classified_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.workflow_status == "CLASSIFIED",
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        classified_count = self._db.execute(classified_stmt).scalar() or 0

        pending_stmt = select(func.count(WorkflowRequest.id)).where(
            WorkflowRequest.workflow_status == "PENDING",
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        pending_count = self._db.execute(pending_stmt).scalar() or 0

        # Failure detection (count records with NULL priority after classification attempt)
        # This is a heuristic: if classified but priority is still NULL, it may indicate failure
        failed_workflows = 0  # Can be enhanced with error tracking table in future
        
        # Retry attempts (count duplicates by user_id within same date)
        # For now, estimate based on workflow patterns
        retry_attempts = 0  # Can be enhanced with retry tracking in future

        # Average confidence score
        avg_confidence_stmt = select(func.avg(WorkflowRequest.confidence_score)).where(
            WorkflowRequest.confidence_score.isnot(None),
            WorkflowRequest.created_at >= start_of_day,
            WorkflowRequest.created_at <= end_of_day,
        )
        avg_confidence = self._db.execute(avg_confidence_stmt).scalar()
        avg_confidence_score = float(avg_confidence) if avg_confidence else None

        logger.info(
            "analytics_aggregation_complete",
            extra={
                "event": "analytics_aggregation_complete",
                "report_date": str(report_date),
                "total_requests": total_requests,
                "high_priority": high_priority_count,
            },
        )

        return {
            "total_requests": total_requests,
            "high_priority_count": high_priority_count,
            "medium_priority_count": medium_priority_count,
            "low_priority_count": low_priority_count,
            "research_completed_count": research_completed_count,
            "classified_count": classified_count,
            "pending_count": pending_count,
            "failed_workflows": failed_workflows,
            "retry_attempts": retry_attempts,
            "avg_confidence_score": avg_confidence_score,
        }
