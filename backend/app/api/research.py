from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_workflow_db
from app.schemas.research import ResearchAgentRequest, ResearchAgentResponse
from app.services.workflow.research_service import (
    ResearchAgentError,
    ResearchAgentService,
)


router = APIRouter(prefix="/research", tags=["research"])
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=ResearchAgentResponse)
async def research_analyze(
    payload: ResearchAgentRequest,
    db: Session = Depends(get_workflow_db),
) -> ResearchAgentResponse:
    """
    Execute AI-powered research analysis on a given topic.
    
    This endpoint is triggered ONLY for HIGH priority + RESEARCH category tasks
    from the N8N workflow automation system.
    
    Process:
    1. Validates request and workflow context
    2. Initializes research agent with LiteLLM
    3. Performs deep analysis with structured reasoning
    4. Persists results to PostgreSQL
    5. Updates workflow status to RESEARCH_COMPLETED
    6. Returns structured research output
    """
    service = ResearchAgentService(db)

    try:
        analysis = await service.execute_research(payload)
    except ResearchAgentError as exc:
        logger.warning("research_analysis_error", extra={"error": str(exc)})
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("research_unhandled_error")
        raise HTTPException(status_code=500, detail="Research analysis failed") from exc

    return ResearchAgentResponse(
        success=True,
        request_id=payload.request_id,
        workflow_status="RESEARCH_COMPLETED",
        research_result=analysis,
    )
