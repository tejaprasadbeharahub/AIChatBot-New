import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


ProviderType = Literal["postgresql", "mysql", "sqlserver", "sqlite"]
ExecutionStatusType = Literal["pending", "succeeded", "failed"]
OperationType = Literal[
    "read",
    "insert",
    "update",
    "delete",
    "upsert",
    "schema_create",
    "schema_alter",
    "schema_drop",
    "schema_index",
    "schema_view",
    "transaction",
    "admin",
    "unknown",
]
RiskLevelType = Literal["low", "medium", "high", "critical"]
ApprovalStatusType = Literal["pending", "approved", "rejected", "auto_approved", "executed"]


class DBConnectionBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    provider: ProviderType
    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    database_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    sqlite_path: str | None = Field(default=None, max_length=500)
    extra_options: dict[str, Any] = Field(default_factory=dict)


class DBConnectionCreate(DBConnectionBase):
    password: str | None = Field(default=None, max_length=1024)

    @field_validator("sqlite_path")
    @classmethod
    def validate_sqlite_path(cls, value: str | None) -> str | None:
        if value is None:
            return value
        trimmed = value.strip()
        return trimmed or None


class DBConnectionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    host: str | None = Field(default=None, max_length=255)
    port: int | None = Field(default=None, ge=1, le=65535)
    database_name: str | None = Field(default=None, max_length=255)
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=1024)
    sqlite_path: str | None = Field(default=None, max_length=500)
    extra_options: dict[str, Any] | None = None
    is_active: bool | None = None


class DBConnectionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    provider: ProviderType
    host: str | None
    port: int | None
    database_name: str | None
    username: str | None
    sqlite_path: str | None
    extra_options: dict[str, Any] | None = Field(default_factory=dict)
    is_active: bool
    has_password: bool
    last_validated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DBConnectionValidationResponse(BaseModel):
    success: bool
    message: str


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    nullable: bool


class RelationshipMetadata(BaseModel):
    constrained_columns: list[str]
    referred_table: str | None
    referred_columns: list[str]


class TableMetadata(BaseModel):
    table_name: str
    columns: list[ColumnMetadata]
    relationships: list[RelationshipMetadata]


class SchemaMetadataResponse(BaseModel):
    connection_id: uuid.UUID
    tables: list[TableMetadata]


class ExecuteNLQueryRequest(BaseModel):
    connection_id: uuid.UUID
    question: str = Field(min_length=1, max_length=4000)
    chat_id: uuid.UUID | None = None
    max_rows: int | None = Field(default=None, ge=1, le=5000)


class SQLQueryExecutionRead(BaseModel):
    id: uuid.UUID
    connection_id: uuid.UUID
    user_id: uuid.UUID
    chat_id: uuid.UUID
    message_id: uuid.UUID | None
    user_question: str
    generated_sql: str
    sql_explanation: str | None
    execution_status: ExecutionStatusType
    error_message: str | None
    execution_started_at: datetime
    execution_finished_at: datetime | None
    execution_duration_ms: int | None
    row_count: int | None
    returned_columns: list[str] = Field(default_factory=list)
    result_rows: list[dict[str, Any]] = Field(default_factory=list)
    retry_count: int
    operation_type: OperationType | None = None
    risk_level: RiskLevelType | None = None
    risk_messages: list[str] = Field(default_factory=list)
    approval_status: ApprovalStatusType | None = None

    model_config = {"from_attributes": True}


class AIGeneratedSQLResponse(BaseModel):
    """Structured response from AI SQL generation with validation metadata."""
    operation_type: OperationType
    sql: str
    explanation: str | None = None
    warnings: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    validation_passed: bool = True


class AIResponseValidationFailure(BaseModel):
    """Response when AI generates non-SQL or invalid output."""
    success: bool = False
    error_type: str  # "refusal", "explanation", "clarification", "invalid_sql", "malformed", "conversational"
    error_message: str
    user_friendly_message: str
    ai_response_preview: str = Field(max_length=500)
    suggested_action: str | None = None


class ExecuteNLQueryResponse(BaseModel):
    chat_id: uuid.UUID
    user_message_id: uuid.UUID
    assistant_message_id: uuid.UUID
    reply: str
    execution: SQLQueryExecutionRead
    approval_request: OperationApprovalRequest | None = None


class SQLQueryHistoryResponse(BaseModel):
    items: list[SQLQueryExecutionRead]


class OperationApprovalRequest(BaseModel):
    operation_type: OperationType
    risk_level: RiskLevelType
    risk_messages: list[str]
    generated_sql: str
    sql_explanation: str | None
    user_question: str


class ApproveOperationRequest(BaseModel):
    execution_id: uuid.UUID
    approved: bool
    reason: str = ""


class ApprovalStatusResponse(BaseModel):
    execution_id: uuid.UUID
    approval_status: ApprovalStatusType
    operation_type: OperationType
    risk_level: RiskLevelType
    risk_messages: list[str]
    generated_sql: str
    sql_explanation: str | None
    user_question: str
    is_approved: bool
    is_rejected: bool
    is_pending: bool
