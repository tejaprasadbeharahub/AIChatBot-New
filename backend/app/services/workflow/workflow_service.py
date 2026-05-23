from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.workflow_request import WorkflowRequest
from app.schemas.workflow import WorkflowTaskRequest


logger = logging.getLogger(__name__)


class WorkflowServiceError(Exception):
    """Raised when workflow request persistence fails."""


@dataclass(slots=True)
class WorkflowClassification:
    """LLM enrichment output contract for future workflow categorization steps."""

    category: str | None = None
    priority: str | None = None
    confidence_score: float | None = None


class WorkflowService:
    """Service layer for workflow task creation."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def _classify_with_litellm(self, payload: WorkflowTaskRequest) -> WorkflowClassification:
        """LiteLLM-ready seam for future categorization without changing API contract.

        This API intentionally persists requests as PENDING with null classification fields.
        Later Project APIs can call LiteLLM and update category/priority/confidence.
        """
        _ = payload
        _ = settings.litellm_proxy_url
        _ = settings.litellm_api_key
        return WorkflowClassification()

    def create_workflow_request(self, payload: WorkflowTaskRequest) -> WorkflowRequest:
        """Persist workflow request in PENDING state for downstream N8N processing."""
        workflow_request = WorkflowRequest(
            user_id=payload.user_id,
            user_message=payload.message,
            category=None,
            priority=None,
            confidence_score=None,
            workflow_status="PENDING",
        )

        try:
            self._db.add(workflow_request)
            self._db.commit()
            self._db.refresh(workflow_request)
        except SQLAlchemyError as exc:
            self._db.rollback()
            logger.exception(
                "workflow_request_create_failed",
                extra={
                    "event": "workflow_request_create_failed",
                    "user_id": payload.user_id,
                },
            )
            raise WorkflowServiceError("Failed to create workflow request") from exc

        logger.info(
            "workflow_request_created",
            extra={
                "event": "workflow_request_created",
                "request_id": str(workflow_request.id),
                "user_id": workflow_request.user_id,
                "workflow_status": workflow_request.workflow_status,
            },
        )
        return workflow_request
