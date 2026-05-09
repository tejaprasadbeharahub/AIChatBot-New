"""create_pdf_documents_table

Revision ID: e7a1b9c3d4f5
Revises: d1e2f3g4h5i6
Create Date: 2026-05-09 12:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e7a1b9c3d4f5"
down_revision: Union[str, None] = "d1e2f3g4h5i6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="pdf_embedding_status",
        create_type=False,
    )
    status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "pdf_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("attachment_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("storage_path", sa.String(length=500), nullable=False),
        sa.Column("status", status_enum, nullable=False, server_default="pending"),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column("embedding_model", sa.String(length=255), nullable=True),
        sa.Column("vector_collection_id", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("upload_timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attachment_id"], ["attachments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(op.f("ix_pdf_documents_attachment_id"), "pdf_documents", ["attachment_id"], unique=False)
    op.create_index(op.f("ix_pdf_documents_message_id"), "pdf_documents", ["message_id"], unique=False)
    op.create_index(op.f("ix_pdf_documents_chat_id"), "pdf_documents", ["chat_id"], unique=False)
    op.create_index(op.f("ix_pdf_documents_user_id"), "pdf_documents", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_pdf_documents_user_id"), table_name="pdf_documents")
    op.drop_index(op.f("ix_pdf_documents_chat_id"), table_name="pdf_documents")
    op.drop_index(op.f("ix_pdf_documents_message_id"), table_name="pdf_documents")
    op.drop_index(op.f("ix_pdf_documents_attachment_id"), table_name="pdf_documents")
    op.drop_table("pdf_documents")

    status_enum = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="pdf_embedding_status",
    )
    status_enum.drop(op.get_bind(), checkfirst=True)
