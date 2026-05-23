from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class WorkflowTaskRequest(BaseModel):
    user_id: str = Field(..., description="Frontend user identifier")
    message: str = Field(..., min_length=5, description="Workflow request message")

    @field_validator("user_id", mode="before")
    @classmethod
    def normalize_user_id(cls, value: object) -> str:
        if value is None:
            raise ValueError("user_id is required")
        if not isinstance(value, str):
            raise ValueError("user_id must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("user_id is required")
        return normalized

    @field_validator("message", mode="before")
    @classmethod
    def normalize_message(cls, value: object) -> str:
        if value is None:
            raise ValueError("message is required")
        if not isinstance(value, str):
            raise ValueError("message must be a string")
        normalized = value.strip()
        if not normalized:
            raise ValueError("message is required")
        if len(normalized) < 5:
            raise ValueError("message must be at least 5 characters")
        return normalized


class WorkflowTaskResponse(BaseModel):
    success: bool
    request_id: UUID
    message: str
    status: str
