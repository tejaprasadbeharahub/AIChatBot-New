import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

ExecutionStatusEnum = Enum("pending", "succeeded", "failed", name="sql_execution_status")
OperationTypeEnum = Enum(
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
    name="operation_type",
)
RiskLevelEnum = Enum("low", "medium", "high", "critical", name="risk_level")
ApprovalStatusEnum = Enum(
    "pending",
    "approved",
    "rejected",
    "auto_approved",
    "executed",
    name="approval_status",
)


class SQLQueryExecution(Base):
    __tablename__ = "sql_query_executions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("db_connections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True, index=True
    )

    user_question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    sql_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(ExecutionStatusEnum, default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    operation_type: Mapped[str | None] = mapped_column(OperationTypeEnum, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(RiskLevelEnum, nullable=True)
    risk_messages: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    approval_status: Mapped[str | None] = mapped_column(ApprovalStatusEnum, nullable=True)

    execution_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    execution_finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    returned_columns: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    result_rows: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    connection: Mapped["DBConnection"] = relationship("DBConnection", back_populates="sql_query_executions")  # noqa: F821
    user: Mapped["User"] = relationship("User", back_populates="sql_query_executions")  # noqa: F821
    chat: Mapped["Chat"] = relationship("Chat", back_populates="sql_query_executions")  # noqa: F821
    message: Mapped["Message"] = relationship("Message", back_populates="sql_query_executions")  # noqa: F821
