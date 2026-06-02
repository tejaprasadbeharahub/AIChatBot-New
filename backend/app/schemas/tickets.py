from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


TicketStatus = Literal["OPEN", "IN_PROGRESS", "CLOSED"]
WorkflowState = Literal["WAITING", "RUNNING", "COMPLETED", "CLOSED"]


class FarmTicketCreateRequest(BaseModel):
    farmer_name: str = Field(..., min_length=2)
    farmer_email: str = Field(..., min_length=5)
    query: str = Field(..., min_length=5)
    crop_type: str = Field(..., min_length=2)
    location: str = Field(..., min_length=2)
    weather: str = Field(..., min_length=2)


class TicketStatusUpdateRequest(BaseModel):
    ticket_id: int
    ticket_status: TicketStatus


class FarmTicketResponse(BaseModel):
    ticket_id: int
    farmer_name: str
    farmer_email: str
    query: str
    crop_type: str
    location: str
    weather: str
    ticket_status: TicketStatus
    workflow_state: WorkflowState
    risk_level: str | None = None
    ai_confidence: float | None = None
    resume_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    extra: dict[str, Any] = Field(default_factory=dict)


class FarmTicketListResponse(BaseModel):
    success: bool
    records: list[FarmTicketResponse]


class TicketMutationResponse(BaseModel):
    success: bool
    message: str
    record: FarmTicketResponse
