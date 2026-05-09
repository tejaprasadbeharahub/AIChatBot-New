import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── AI chat (LLM request/response) ──────────────────────────────────────────

class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    # Deprecated for normal flow. Backend derives thread memory from persisted messages.
    history: list[ChatMessage] = Field(default_factory=list)
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    chat_id: uuid.UUID | None = None  # optional: persist to an existing chat


class ChatResponse(BaseModel):
    reply: str
    model: str
    chat_id: uuid.UUID


# ── Persisted chat (DB) ──────────────────────────────────────────────────────

class ChatRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatCreate(BaseModel):
    title: str | None = None


class ChatUpdateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
