import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.generated_image import GeneratedImageRead


class AttachmentRef(BaseModel):
    """Simple attachment reference for message responses"""
    id: uuid.UUID
    file_name: str
    file_type: str
    mime_type: str
    file_size: int
    upload_timestamp: datetime

    model_config = {"from_attributes": True}


class MessageRead(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    role: Literal["user", "assistant"]
    content: str
    timestamp: datetime
    attachments: list[AttachmentRef] = Field(default_factory=list)
    generated_images: list[GeneratedImageRead] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class MessageCreateRequest(BaseModel):
    content: str
