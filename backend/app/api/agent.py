from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_workflow_db
from app.schemas.agent import AgentClassifyRequest, AgentClassifyResponse
from app.services.workflow.classification_service import (
    AgentClassificationError,
    AgentClassificationService,
)


router = APIRouter(prefix="/agent", tags=["agent"])
logger = logging.getLogger(__name__)


@router.post("/classify", response_model=AgentClassifyResponse)
async def classify_task(
    payload: AgentClassifyRequest,
    db: Session = Depends(get_workflow_db),
) -> AgentClassifyResponse:
    """Classify workflow message via LiteLLM and persist classification into workflow_requests."""
    service = AgentClassificationService(db)

    try:
        result = await service.classify_and_update(payload)
    except AgentClassificationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("agent_classification_unhandled_error")
        raise HTTPException(status_code=500, detail="Agent classification failed") from exc

    return AgentClassifyResponse(
        success=True,
        priority=result.priority,
        category=result.category,
        confidence=result.confidence,
        workflow_status="CLASSIFIED",
    )
