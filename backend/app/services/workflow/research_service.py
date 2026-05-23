from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any

from litellm import acompletion
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.research_prompt import (
    RESEARCH_REASONING_PROMPT,
    RESEARCH_SYSTEM_PROMPT,
)
from app.core.config import settings
from app.models.research_result import ResearchResult
from app.models.workflow_request import WorkflowRequest
from app.schemas.research import (
    ResearchAgentRequest,
    ResearchAnalysisResult,
)

logger = logging.getLogger(__name__)


class ResearchAgentError(Exception):
    """Raised when research agent analysis or DB persistence fails."""


class ResearchAgentService:
    """Service for AI-powered research analysis with LiteLLM and database persistence."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _resolve_model(self) -> str:
        """Resolve the LLM model to use for research analysis."""
        return (
            settings.n8n_classification_model
            or settings.llm_model
            or "gpt-4o"
        )

    def _extract_json(self, text: str) -> dict[str, Any]:
        """Extract JSON from LLM response, handling markdown fences and inline JSON."""
        content = text.strip()

        # Try markdown-fenced JSON first
        fenced_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", content, re.DOTALL)
        if fenced_match:
            content = fenced_match.group(1).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try inline JSON as fallback
            inline_match = re.search(r"\{.*\}", content, re.DOTALL)
            if inline_match:
                return json.loads(inline_match.group(0))
            raise

    async def _run_research_agent(self, message: str) -> ResearchAnalysisResult:
        """Execute research agent via LiteLLM with retry and timeout handling."""
        retries = max(settings.n8n_classification_retry_attempts, 1)
        timeout_seconds = max(settings.n8n_classification_timeout_seconds, 30)
        model_name = self._resolve_model()

        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                # Prepare reasoning prompt with the specific message
                reasoning_prompt = RESEARCH_REASONING_PROMPT.format(message=message)

                response = await asyncio.wait_for(
                    acompletion(
                        model=model_name,
                        base_url=settings.litellm_proxy_url,
                        api_key=settings.litellm_api_key,
                        temperature=0.3,
                        messages=[
                            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
                            {"role": "user", "content": reasoning_prompt},
                        ],
                    ),
                    timeout=timeout_seconds,
                )

                content = response.choices[0].message.content if response.choices else ""
                parsed = self._extract_json(str(content or ""))
                return ResearchAnalysisResult.model_validate(parsed)

            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "research_agent_retry",
                    extra={
                        "event": "research_agent_retry",
                        "attempt": attempt,
                        "max_attempts": retries,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

            except Exception as exc:  # pragma: no cover - provider/network errors
                last_error = exc
                logger.warning(
                    "research_agent_provider_error",
                    extra={
                        "event": "research_agent_provider_error",
                        "attempt": attempt,
                        "max_attempts": retries,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(min(0.3 * attempt, 2.0))

        # Fallback for resilience in automation pipelines
        if settings.n8n_classification_enable_fallback:
            logger.warning(
                "research_agent_fallback_used",
                extra={
                    "event": "research_agent_fallback_used",
                    "error": str(last_error),
                },
            )
            return ResearchAnalysisResult(
                summary="Research analysis completed with fallback defaults.",
                key_points=["Analysis completed", "Further research recommended"],
                recommendations=["Continue deep analysis", "Consult domain experts"],
                risks=["Incomplete analysis", "Limited time for verification"],
                next_steps=["Schedule follow-up analysis", "Verify findings with domain experts"],
                confidence_score=45,
            )

        raise ResearchAgentError(f"Research analysis failed: {last_error}")

    def _find_workflow_request(self, request_id: str) -> WorkflowRequest:
        """Fetch workflow request from database."""
        stmt = select(WorkflowRequest).where(WorkflowRequest.id == request_id)
        workflow_request = self._db.execute(stmt).scalars().first()

        if workflow_request is None:
            raise ResearchAgentError(f"Workflow request not found: {request_id}")

        return workflow_request

    def _persist_research_result(
        self,
        request_id: str,
        analysis: ResearchAnalysisResult,
    ) -> ResearchResult:
        """Persist research analysis to database and update workflow status."""
        try:
            # Create research result record
            research_result = ResearchResult(
                request_id=request_id,
                summary=analysis.summary,
                key_points=analysis.key_points,
                recommendations=analysis.recommendations,
                risks=analysis.risks,
                next_steps=analysis.next_steps,
                confidence_score=analysis.confidence_score,
            )

            self._db.add(research_result)

            # Update workflow request status to RESEARCH_COMPLETED
            stmt = update(WorkflowRequest).where(
                WorkflowRequest.id == request_id
            ).values(workflow_status="RESEARCH_COMPLETED")
            self._db.execute(stmt)

            self._db.commit()
            self._db.refresh(research_result)

        except SQLAlchemyError as exc:
            self._db.rollback()
            logger.exception("research_result_persistence_failed")
            raise ResearchAgentError("Failed to persist research results") from exc

        logger.info(
            "research_result_persisted",
            extra={
                "event": "research_result_persisted",
                "request_id": str(request_id),
                "confidence_score": analysis.confidence_score,
            },
        )
        return research_result

    async def execute_research(self, payload: ResearchAgentRequest) -> ResearchAnalysisResult:
        """Execute complete research workflow: validate, analyze, persist."""
        # Verify workflow request exists
        workflow_request = self._find_workflow_request(payload.request_id)
        logger.info(
            "research_started",
            extra={
                "event": "research_started",
                "request_id": str(payload.request_id),
                "message": payload.message[:100],
            },
        )

        # Run research agent
        analysis = await self._run_research_agent(payload.message)

        # Persist results and update workflow status
        self._persist_research_result(payload.request_id, analysis)

        logger.info(
            "research_completed",
            extra={
                "event": "research_completed",
                "request_id": str(payload.request_id),
                "confidence": analysis.confidence_score,
            },
        )

        return analysis
