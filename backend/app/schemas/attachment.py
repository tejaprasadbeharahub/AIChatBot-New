import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AttachmentCreate(BaseModel):
    """Schema for creating attachments (from file upload)"""
    file_name: str = Field(..., min_length=1, max_length=255)
    file_type: Literal["image", "video", "code", "formula", "document"] = Field(...)
    mime_type: str = Field(..., max_length=100)
    file_size: int = Field(..., gt=0)
    storage_path: str = Field(..., max_length=500)


class AttachmentRead(BaseModel):
    """Schema for reading attachment data"""
    id: uuid.UUID
    message_id: uuid.UUID
    file_name: str
    file_type: str
    mime_type: str
    file_size: int
    storage_path: str
    upload_timestamp: datetime

    model_config = {"from_attributes": True}


class AttachmentDelete(BaseModel):
    """Schema for deleting attachments"""
    id: uuid.UUID


class AttachmentMetadata(BaseModel):
    """Simplified metadata for attachment responses"""
    id: uuid.UUID
    file_name: str
    file_type: str
    mime_type: str
    file_size: int
    upload_timestamp: datetime

    model_config = {"from_attributes": True}


class AttachmentTextExtraction(BaseModel):
    attachment_id: uuid.UUID
    attachment_type: str
    extracted_text: str
    summary_text: str
