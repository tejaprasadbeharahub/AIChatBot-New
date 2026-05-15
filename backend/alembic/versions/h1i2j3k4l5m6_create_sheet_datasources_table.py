"""h1i2j3k4l5m6_create_sheet_datasources_table

Revision ID: h1i2j3k4l5m6
Revises: g8h9i0j1k2l3
Create Date: 2026-05-15 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "h1i2j3k4l5m6"
down_revision: Union[str, None] = "g8h9i0j1k2l3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    source_type_enum = postgresql.ENUM(
        "csv", "xlsx", "google_sheets",
        name="sheet_datasource_type",
        create_type=False,
    )
    source_type_enum.create(op.get_bind(), checkfirst=True)

    status_enum = postgresql.ENUM(
        "pending", "processing", "ready", "failed",
        name="sheet_datasource_status",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "sheet_datasources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", source_type_enum, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=True),
        sa.Column("storage_path", sa.String(500), nullable=True),
        sa.Column("file_size_bytes", sa.Integer, nullable=True),
        sa.Column("sheet_url", sa.Text, nullable=True),
        sa.Column("sheet_id", sa.String(255), nullable=True),
        sa.Column("sheet_tab", sa.String(255), nullable=True),
        sa.Column("status", status_enum, nullable=False, server_default="pending"),
        sa.Column("row_count", sa.Integer, nullable=True),
        sa.Column("column_count", sa.Integer, nullable=True),
        sa.Column("column_names", sa.Text, nullable=True),
        sa.Column("sheet_tabs", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sheet_datasources_chat_id", "sheet_datasources", ["chat_id"])
    op.create_index("ix_sheet_datasources_user_id", "sheet_datasources", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sheet_datasources_user_id", table_name="sheet_datasources")
    op.drop_index("ix_sheet_datasources_chat_id", table_name="sheet_datasources")
    op.drop_table("sheet_datasources")

    postgresql.ENUM(name="sheet_datasource_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="sheet_datasource_type").drop(op.get_bind(), checkfirst=True)
