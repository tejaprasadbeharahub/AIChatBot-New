import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


SheetDatasourceTypeEnum = Enum(
    "csv",
    "xlsx",
    "google_sheets",
    name="sheet_datasource_type",
)

SheetDatasourceStatusEnum = Enum(
    "pending",
    "processing",
    "ready",
    "failed",
    name="sheet_datasource_status",
)


class SheetDatasource(Base):
    __tablename__ = "sheet_datasources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    source_type: Mapped[str] = mapped_column(SheetDatasourceTypeEnum, nullable=False)

    # File-based (CSV / XLSX)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Google Sheets
    sheet_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    sheet_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sheet_tab: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Metadata populated after loading
    status: Mapped[str] = mapped_column(SheetDatasourceStatusEnum, nullable=False, default="pending")
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    column_names: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded list
    sheet_tabs: Mapped[str | None] = mapped_column(Text, nullable=True)    # JSON-encoded list for xlsx
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    chat: Mapped["Chat"] = relationship("Chat")  # noqa: F821
    user: Mapped["User"] = relationship("User")  # noqa: F821
