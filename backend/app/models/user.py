import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    chats: Mapped[list["Chat"]] = relationship(  # noqa: F821
        "Chat", back_populates="user", cascade="all, delete-orphan"
    )
    db_connections: Mapped[list["DBConnection"]] = relationship(  # noqa: F821
        "DBConnection", back_populates="user", cascade="all, delete-orphan"
    )
    sql_query_executions: Mapped[list["SQLQueryExecution"]] = relationship(  # noqa: F821
        "SQLQueryExecution", back_populates="user", cascade="all, delete-orphan"
    )
