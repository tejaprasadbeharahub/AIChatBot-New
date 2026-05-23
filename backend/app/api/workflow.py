from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_workflow_db
from app.schemas.workflow import WorkflowTaskRequest, WorkflowTaskResponse
from app.services.workflow.workflow_service import WorkflowService, WorkflowServiceError


router = APIRouter(prefix="/workflow", tags=["workflow"])
logger = logging.getLogger(__name__)


@router.post("/task", response_model=WorkflowTaskResponse, status_code=201)
async def create_workflow_task(
    payload: WorkflowTaskRequest,
    db: Session = Depends(get_workflow_db),
) -> WorkflowTaskResponse:
    """Create workflow request record that can be consumed by the N8N automation pipeline."""
    service = WorkflowService(db)

    try:
        request_row = service.create_workflow_request(payload)
    except WorkflowServiceError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.exception("workflow_task_unhandled_error")
        raise HTTPException(status_code=500, detail="Workflow task creation failed") from exc

    return WorkflowTaskResponse(
        success=True,
        request_id=request_row.id,
        message="Workflow request created successfully",
        status=request_row.workflow_status,
    )
