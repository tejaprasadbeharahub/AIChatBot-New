import json
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


SourceType = Literal["csv", "xlsx", "google_sheets"]
DatasourceStatus = Literal["pending", "processing", "ready", "failed"]


class SheetDatasourceRead(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    user_id: uuid.UUID
    source_type: SourceType
    file_name: str | None
    storage_path: str | None
    file_size_bytes: int | None
    sheet_url: str | None
    sheet_id: str | None
    sheet_tab: str | None
    status: DatasourceStatus
    row_count: int | None
    column_count: int | None
    column_names: list[str] | None
    sheet_tabs: list[str] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Deserialize JSON-encoded column/tab lists stored as Text
        if hasattr(obj, "__dict__"):
            data = {c.key: getattr(obj, c.key) for c in obj.__table__.columns}
            for field in ("column_names", "sheet_tabs"):
                raw = data.get(field)
                if isinstance(raw, str):
                    try:
                        data[field] = json.loads(raw)
                    except (ValueError, TypeError):
                        data[field] = None
            return cls(**data)
        return super().model_validate(obj, **kwargs)


class SheetUploadResponse(BaseModel):
    datasource: SheetDatasourceRead


class ConnectGoogleSheetRequest(BaseModel):
    chat_id: uuid.UUID
    sheet_url: str = Field(min_length=1, max_length=2000)
    sheet_tab: str | None = Field(default=None, max_length=255)

    @field_validator("sheet_url")
    @classmethod
    def validate_sheet_url(cls, v: str) -> str:
        if "docs.google.com/spreadsheets" not in v:
            raise ValueError("URL must be a valid Google Sheets URL")
        return v.strip()


class ConnectGoogleSheetResponse(BaseModel):
    datasource: SheetDatasourceRead


class SheetQueryRequest(BaseModel):
    datasource_id: uuid.UUID
    question: str = Field(min_length=1, max_length=4000)
    chat_id: uuid.UUID | None = None
    sheet_tab: str | None = None


class SheetQueryTableRow(BaseModel):
    columns: list[str]
    rows: list[list[str]]


class SheetQueryResponse(BaseModel):
    chat_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    datasource_id: uuid.UUID
    question: str
    answer: str
    table: SheetQueryTableRow | None = None
    execution_duration_ms: int


class ListDatasourcesResponse(BaseModel):
    items: list[SheetDatasourceRead]
