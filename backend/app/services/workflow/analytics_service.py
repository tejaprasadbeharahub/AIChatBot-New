from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import date, datetime, timezone
from typing import Any

from litellm import acompletion
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.analytics_prompt import (
    ANALYTICS_REASONING_PROMPT,
    ANALYTICS_SYSTEM_PROMPT,
)
from app.core.config import settings
from app.models.daily_report import DailyReport
from app.schemas.daily_summary import AnalyticsReport
from app.services.workflow.analytics_aggregation import AnalyticsAggregationService

logger = logging.getLogger(__name__)


class AnalyticsAgentError(Exception):
    """Raised when analytics generation or DB persistence fails."""


class AnalyticsAgentService:
    """Service for AI-powered analytics summary generation."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _resolve_model(self) -> str:
        """Resolve LLM model for analytics."""
        return (
            settings.n8n_classification_model
            or settings.llm_model
            or "gpt-4o"
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response."""
        content = text.strip()

        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if fenced_match:
            content = fenced_match.group(1).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            inline_match = re.search(r"\{.*\}", content, re.DOTALL)
            if inline_match:
                return json.loads(inline_match.group(0))
            raise

    async def _generate_analytics_report(
        self, metrics: dict, report_date: date
    ) -> AnalyticsReport:
        """Generate analytics report via LiteLLM."""
        retries = max(settings.n8n_classification_retry_attempts, 1)
        timeout_seconds = max(settings.n8n_classification_timeout_seconds, 30)
        model_name = self._resolve_model()

        last_error: Exception | None = None

        # Format prompt with metrics
        reasoning_prompt = ANALYTICS_REASONING_PROMPT.format(
            total_requests=metrics["total_requests"],
            high_priority_count=metrics["high_priority_count"],
            medium_priority_count=metrics["medium_priority_count"],
            low_priority_count=metrics["low_priority_count"],
            classified_count=metrics["classified_count"],
            research_completed_count=metrics["research_completed_count"],
            pending_count=metrics["pending_count"],
            failed_workflows=metrics["failed_workflows"],
            retry_attempts=metrics["retry_attempts"],
            avg_confidence_score=round(metrics["avg_confidence_score"], 2) if metrics["avg_confidence_score"] else 0,
        )

        for attempt in range(1, retries + 1):
            try:
                response = await asyncio.wait_for(
                    acompletion(
                        model=model_name,
                        base_url=settings.litellm_proxy_url,
                        api_key=settings.litellm_api_key,
                        temperature=0.2,
                        messages=[
                            {"role": "system", "content": ANALYTICS_SYSTEM_PROMPT},
                            {"role": "user", "content": reasoning_prompt},
                        ],
                    ),
                    timeout=timeout_seconds,
                )

                content = response.choices[0].message.content if response.choices else ""
                parsed = self._extract_json(str(content or ""))
                return AnalyticsReport.model_validate(parsed)

            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "analytics_generation_retry",
                    extra={
                        "event": "analytics_generation_retry",
                        "attempt": attempt,
                        "max_attempts": retries,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

            except Exception as exc:  # pragma: no cover
                last_error = exc
                logger.warning(
                    "analytics_generation_provider_error",
                    extra={
                        "event": "analytics_generation_provider_error",
                        "attempt": attempt,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

        # Fallback analytics
        if settings.n8n_classification_enable_fallback:
            logger.warning(
                "analytics_generation_fallback_used",
                extra={
                    "event": "analytics_generation_fallback_used",
                    "error": str(last_error),
                },
            )
            return AnalyticsReport(
                executive_summary="Daily operations summary generated with fallback defaults.",
                key_insights=[
                    "Standard workflow processing completed",
                    "Metrics collected and aggregated",
                ],
                risks=["Potential AI analysis limitations"],
                recommendations=[
                    "Review workflow performance metrics",
                    "Optimize high-priority task handling",
                ],
                workflow_efficiency_score=70,
            )

        raise AnalyticsAgentError(f"Analytics generation failed: {last_error}")

    def _persist_analytics_report(
        self,
        report_date: date,
        metrics: dict,
        analytics: AnalyticsReport,
    ) -> DailyReport:
        """Persist analytics report to database."""
        try:
            # Check if report already exists for this date
            existing_stmt = select(DailyReport).where(DailyReport.report_date == report_date)
            existing = self._db.execute(existing_stmt).scalars().first()

            if existing:
                # Update existing report
                existing.total_requests = metrics["total_requests"]
                existing.high_priority_count = metrics["high_priority_count"]
                existing.medium_priority_count = metrics["medium_priority_count"]
                existing.low_priority_count = metrics["low_priority_count"]
                existing.research_completed_count = metrics["research_completed_count"]
                existing.classified_count = metrics["classified_count"]
                existing.pending_count = metrics["pending_count"]
                existing.failed_workflows = metrics["failed_workflows"]
                existing.retry_attempts = metrics["retry_attempts"]
                existing.avg_confidence_score = metrics["avg_confidence_score"]
                existing.ai_summary = analytics.executive_summary
                existing.key_insights = analytics.key_insights
                existing.risks = analytics.risks
                existing.recommendations = analytics.recommendations
                existing.workflow_efficiency_score = analytics.workflow_efficiency_score
                existing.generated_at = datetime.now(timezone.utc)
                report = existing
            else:
                # Create new report
                report = DailyReport(
                    report_date=report_date,
                    total_requests=metrics["total_requests"],
                    high_priority_count=metrics["high_priority_count"],
                    medium_priority_count=metrics["medium_priority_count"],
                    low_priority_count=metrics["low_priority_count"],
                    research_completed_count=metrics["research_completed_count"],
                    classified_count=metrics["classified_count"],
                    pending_count=metrics["pending_count"],
                    failed_workflows=metrics["failed_workflows"],
                    retry_attempts=metrics["retry_attempts"],
                    avg_confidence_score=metrics["avg_confidence_score"],
                    ai_summary=analytics.executive_summary,
                    key_insights=analytics.key_insights,
                    risks=analytics.risks,
                    recommendations=analytics.recommendations,
                    workflow_efficiency_score=analytics.workflow_efficiency_score,
                )

            self._db.add(report)
            self._db.commit()
            self._db.refresh(report)

        except SQLAlchemyError as exc:
            self._db.rollback()
            logger.exception("analytics_report_persistence_failed")
            raise AnalyticsAgentError("Failed to persist analytics report") from exc

        logger.info(
            "analytics_report_persisted",
            extra={
                "event": "analytics_report_persisted",
                "report_date": str(report_date),
                "efficiency_score": analytics.workflow_efficiency_score,
            },
        )
        return report

    async def generate_daily_summary(self, report_date: date) -> tuple[dict, AnalyticsReport]:
        """Generate complete daily analytics summary."""
        # Aggregate metrics from database
        aggregation_service = AnalyticsAggregationService(self._db)
        metrics = aggregation_service.aggregate_daily_metrics(report_date)

        logger.info(
            "daily_summary_started",
            extra={
                "event": "daily_summary_started",
                "report_date": str(report_date),
                "total_requests": metrics["total_requests"],
            },
        )

        # Generate AI analytics report
        analytics = await self._generate_analytics_report(metrics, report_date)

        # Persist to database
        self._persist_analytics_report(report_date, metrics, analytics)

        logger.info(
            "daily_summary_completed",
            extra={
                "event": "daily_summary_completed",
                "report_date": str(report_date),
                "efficiency": analytics.workflow_efficiency_score,
            },
        )

        return metrics, analytics
