"""Add operation type, risk level, and approval status to sql_query_executions table.

Revision ID: g8h9i0j1k2l3
Revises: f1a2b3c4d5e6
Create Date: 2026-05-15 06:45:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "g8h9i0j1k2l3"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    operation_type = postgresql.ENUM(
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
    operation_type.create(op.get_bind())

    risk_level = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="risk_level",
    )
    risk_level.create(op.get_bind())

    approval_status = postgresql.ENUM(
        "pending",
        "approved",
        "rejected",
        "auto_approved",
        "executed",
        name="approval_status",
    )
    approval_status.create(op.get_bind())

    # Add columns to sql_query_executions table
    op.add_column("sql_query_executions", sa.Column("operation_type", operation_type, nullable=True))
    op.add_column("sql_query_executions", sa.Column("risk_level", risk_level, nullable=True))
    op.add_column(
        "sql_query_executions",
        sa.Column("risk_messages", sa.JSON(), nullable=True),
    )
    op.add_column("sql_query_executions", sa.Column("approval_status", approval_status, nullable=True))


def downgrade() -> None:
    # Drop columns
    op.drop_column("sql_query_executions", "approval_status")
    op.drop_column("sql_query_executions", "risk_messages")
    op.drop_column("sql_query_executions", "risk_level")
    op.drop_column("sql_query_executions", "operation_type")

    # Drop enums
    sa.Enum(name="approval_status").drop(op.get_bind())
    sa.Enum(name="risk_level").drop(op.get_bind())
    sa.Enum(name="operation_type").drop(op.get_bind())
