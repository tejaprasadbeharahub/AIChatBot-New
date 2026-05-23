from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ClassificationPriority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ClassificationCategory(str, Enum):
    RESEARCH = "RESEARCH"
    BUG = "BUG"
    FEATURE = "FEATURE"
    SUPPORT = "SUPPORT"
    DOCUMENTATION = "DOCUMENTATION"
    GENERAL = "GENERAL"


class AgentClassifyRequest(BaseModel):
    message: str = Field(..., min_length=5)

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


class AgentClassificationResult(BaseModel):
    priority: ClassificationPriority
    category: ClassificationCategory
    confidence: int = Field(..., ge=0, le=100)


class AgentClassifyResponse(BaseModel):
    success: bool
    priority: ClassificationPriority
    category: ClassificationCategory
    confidence: int = Field(..., ge=0, le=100)
    workflow_status: str
