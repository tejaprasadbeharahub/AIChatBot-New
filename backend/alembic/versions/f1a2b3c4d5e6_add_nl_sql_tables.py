"""add_nl_sql_tables

Revision ID: f1a2b3c4d5e6
Revises: e7a1b9c3d4f5
Create Date: 2026-05-15 12:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e7a1b9c3d4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    provider_enum = postgresql.ENUM(
        "postgresql",
        "mysql",
        "sqlserver",
        "sqlite",
        name="db_connection_provider",
        create_type=False,
    )
    provider_enum.create(op.get_bind(), checkfirst=True)

    exec_status_enum = postgresql.ENUM(
        "pending",
        "succeeded",
        "failed",
        name="sql_execution_status",
        create_type=False,
    )
    exec_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "db_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("provider", provider_enum, nullable=False),
        sa.Column("host", sa.String(length=255), nullable=True),
        sa.Column("port", sa.Integer(), nullable=True),
        sa.Column("database_name", sa.String(length=255), nullable=True),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("encrypted_password", sa.Text(), nullable=True),
        sa.Column("sqlite_path", sa.String(length=500), nullable=True),
        sa.Column("extra_options", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_db_connections_user_id"), "db_connections", ["user_id"], unique=False)

    op.create_table(
        "sql_query_executions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chat_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("user_question", sa.Text(), nullable=False),
        sa.Column("generated_sql", sa.Text(), nullable=False),
        sa.Column("sql_explanation", sa.Text(), nullable=True),
        sa.Column("execution_status", exec_status_enum, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("execution_finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_duration_ms", sa.Integer(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("returned_columns", sa.JSON(), nullable=True),
        sa.Column("result_rows", sa.JSON(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["db_connections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_sql_query_executions_connection_id"), "sql_query_executions", ["connection_id"], unique=False)
    op.create_index(op.f("ix_sql_query_executions_user_id"), "sql_query_executions", ["user_id"], unique=False)
    op.create_index(op.f("ix_sql_query_executions_chat_id"), "sql_query_executions", ["chat_id"], unique=False)
    op.create_index(op.f("ix_sql_query_executions_message_id"), "sql_query_executions", ["message_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_sql_query_executions_message_id"), table_name="sql_query_executions")
    op.drop_index(op.f("ix_sql_query_executions_chat_id"), table_name="sql_query_executions")
    op.drop_index(op.f("ix_sql_query_executions_user_id"), table_name="sql_query_executions")
    op.drop_index(op.f("ix_sql_query_executions_connection_id"), table_name="sql_query_executions")
    op.drop_table("sql_query_executions")

    op.drop_index(op.f("ix_db_connections_user_id"), table_name="db_connections")
    op.drop_table("db_connections")

    exec_status_enum = postgresql.ENUM(
        "pending",
        "succeeded",
        "failed",
        name="sql_execution_status",
    )
    exec_status_enum.drop(op.get_bind(), checkfirst=True)

    provider_enum = postgresql.ENUM(
        "postgresql",
        "mysql",
        "sqlserver",
        "sqlite",
        name="db_connection_provider",
    )
    provider_enum.drop(op.get_bind(), checkfirst=True)
