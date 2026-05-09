import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PdfDocumentRead(BaseModel):
    id: uuid.UUID
    attachment_id: uuid.UUID
    message_id: uuid.UUID
    chat_id: uuid.UUID
    user_id: uuid.UUID
    file_name: str
    storage_path: str
    status: str
    chunk_count: int | None
    embedding_model: str | None
    vector_collection_id: str | None
    error_message: str | None
    upload_timestamp: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


class PdfUploadResponse(BaseModel):
    document: PdfDocumentRead


class PdfQueryRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class PdfChunkMatch(BaseModel):
    chunk_id: str
    content: str
    document_id: uuid.UUID
    file_name: str
    chunk_index: int
    score: float


class PdfQueryResponse(BaseModel):
    query: str
    chat_id: uuid.UUID
    matches: list[PdfChunkMatch]
