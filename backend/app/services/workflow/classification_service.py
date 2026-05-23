from __future__ import annotations

import asyncio
import json
import logging
import re
from dataclasses import dataclass

from litellm import acompletion
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.agents.classification_prompt import CLASSIFICATION_SYSTEM_PROMPT
from app.core.config import settings
from app.models.workflow_request import WorkflowRequest
from app.schemas.agent import AgentClassificationResult, AgentClassifyRequest


logger = logging.getLogger(__name__)


class AgentClassificationError(Exception):
    """Raised when LLM classification or DB persistence fails."""


@dataclass(slots=True)
class _RawLLMResult:
    raw_text: str


class AgentClassificationService:
    """Classifies workflow message and updates corresponding workflow request record."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _resolve_model(self) -> str:
        return (
            settings.n8n_classification_model
            or settings.llm_model
            or "gpt-4o-mini"
        )

    def _extract_json(self, text: str) -> dict[str, object]:
        content = text.strip()

        fenced_match = re.search(r"```(?:json)?\\s*(\\{.*?\\})\\s*```", content, re.DOTALL)
        if fenced_match:
            content = fenced_match.group(1).strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            inline_match = re.search(r"\\{.*\\}", content, re.DOTALL)
            if inline_match:
                return json.loads(inline_match.group(0))
            raise

    async def _classify_with_litellm(self, message: str) -> AgentClassificationResult:
        retries = max(settings.n8n_classification_retry_attempts, 1)
        timeout_seconds = max(settings.n8n_classification_timeout_seconds, 1)
        model_name = self._resolve_model()

        last_error: Exception | None = None

        for attempt in range(1, retries + 1):
            try:
                response = await asyncio.wait_for(
                    acompletion(
                        model=model_name,
                        base_url=settings.litellm_proxy_url,
                        api_key=settings.litellm_api_key,
                        temperature=0,
                        messages=[
                            {"role": "system", "content": CLASSIFICATION_SYSTEM_PROMPT},
                            {"role": "user", "content": message},
                        ],
                    ),
                    timeout=timeout_seconds,
                )
                content = response.choices[0].message.content if response.choices else ""
                parsed = self._extract_json(str(content or ""))
                return AgentClassificationResult.model_validate(parsed)
            except (asyncio.TimeoutError, json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning(
                    "agent_classification_retry",
                    extra={
                        "event": "agent_classification_retry",
                        "attempt": attempt,
                        "max_attempts": retries,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(min(0.2 * attempt, 1.0))
            except Exception as exc:  # pragma: no cover - provider/network errors
                last_error = exc
                logger.warning(
                    "agent_classification_provider_error",
                    extra={
                        "event": "agent_classification_provider_error",
                        "attempt": attempt,
                        "max_attempts": retries,
                        "error": str(exc),
                    },
                )
                await asyncio.sleep(min(0.2 * attempt, 1.0))

        # Fallback classification for resilience in automation pipelines.
        if settings.n8n_classification_enable_fallback:
            logger.warning(
                "agent_classification_fallback_used",
                extra={"event": "agent_classification_fallback_used", "error": str(last_error)},
            )
            return AgentClassificationResult(priority="LOW", category="GENERAL", confidence=35)

        raise AgentClassificationError(f"Classification failed: {last_error}")

    def _find_latest_pending_request(self, message: str) -> WorkflowRequest | None:
        stmt = (
            select(WorkflowRequest)
            .where(WorkflowRequest.user_message == message)
            .where(WorkflowRequest.workflow_status == "PENDING")
            .order_by(WorkflowRequest.created_at.desc())
        )
        return self._db.execute(stmt).scalars().first()

    async def classify_and_update(self, payload: AgentClassifyRequest) -> AgentClassificationResult:
        classification = await self._classify_with_litellm(payload.message)

        workflow_request = self._find_latest_pending_request(payload.message)
        if workflow_request is None:
            raise AgentClassificationError("No matching pending workflow request found for message")

        try:
            workflow_request.priority = classification.priority.value
            workflow_request.category = classification.category.value
            workflow_request.confidence_score = float(classification.confidence)
            workflow_request.workflow_status = "CLASSIFIED"
            self._db.add(workflow_request)
            self._db.commit()
            self._db.refresh(workflow_request)
        except SQLAlchemyError as exc:
            self._db.rollback()
            logger.exception("agent_classification_db_update_failed")
            raise AgentClassificationError("Failed to update workflow request classification") from exc

        logger.info(
            "agent_classification_completed",
            extra={
                "event": "agent_classification_completed",
                "workflow_request_id": str(workflow_request.id),
                "priority": classification.priority.value,
                "category": classification.category.value,
                "confidence": classification.confidence,
            },
        )
        return classification
