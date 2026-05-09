import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class GeneratedImageCreate(BaseModel):
    """Schema for creating image generation requests"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    message_id: uuid.UUID
    chat_id: uuid.UUID


class GeneratedImageRead(BaseModel):
    """Schema for reading generated image data"""
    id: uuid.UUID
    message_id: uuid.UUID
    chat_id: uuid.UUID
    prompt: str
    image_url: str | None
    image_path: str | None
    status: Literal["pending", "completed", "failed"]
    error_message: str | None
    generation_timestamp: datetime
    completion_timestamp: datetime | None

    model_config = {"from_attributes": True}


class GeneratedImageResponse(BaseModel):
    """Response for image generation endpoints"""
    id: uuid.UUID
    status: Literal["pending", "completed", "failed"]
    prompt: str
    image_url: str | None
    message_id: uuid.UUID
    generation_timestamp: datetime
    completion_timestamp: datetime | None
    error_message: str | None = None

    model_config = {"from_attributes": True}


class ImageGenerationRequest(BaseModel):
    """Request body for generating images"""
    prompt: str = Field(..., min_length=1, max_length=2000)
    chat_id: str
    message_id: str
