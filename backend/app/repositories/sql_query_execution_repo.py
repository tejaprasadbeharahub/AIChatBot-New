import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.sql_query_execution import SQLQueryExecution


def create_execution(
    db: Session,
    *,
    connection_id: uuid.UUID,
    user_id: uuid.UUID,
    chat_id: uuid.UUID,
    message_id: uuid.UUID | None,
    user_question: str,
    generated_sql: str,
    sql_explanation: str | None,
    operation_type: str | None = None,
    risk_level: str | None = None,
    risk_messages: list[str] | None = None,
    approval_status: str | None = None,
) -> SQLQueryExecution:
    execution = SQLQueryExecution(
        connection_id=connection_id,
        user_id=user_id,
        chat_id=chat_id,
        message_id=message_id,
        user_question=user_question,
        generated_sql=generated_sql,
        sql_explanation=sql_explanation,
        execution_status="pending",
        operation_type=operation_type,
        risk_level=risk_level,
        risk_messages=risk_messages,
        approval_status=approval_status,
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def mark_success(
    db: Session,
    execution: SQLQueryExecution,
    *,
    duration_ms: int,
    row_count: int,
    returned_columns: list[str],
    result_rows: list[dict],
) -> SQLQueryExecution:
    execution.execution_status = "succeeded"
    execution.execution_duration_ms = duration_ms
    execution.row_count = row_count
    execution.returned_columns = returned_columns
    execution.result_rows = result_rows
    execution.execution_finished_at = datetime.now(timezone.utc)
    execution.error_message = None

    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def mark_failure(db: Session, execution: SQLQueryExecution, *, duration_ms: int, error_message: str) -> SQLQueryExecution:
    execution.execution_status = "failed"
    execution.execution_duration_ms = duration_ms
    execution.execution_finished_at = datetime.now(timezone.utc)
    execution.error_message = error_message

    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def list_history_for_user(
    db: Session,
    *,
    user_id: uuid.UUID,
    chat_id: uuid.UUID | None,
    connection_id: uuid.UUID | None,
    limit: int,
) -> list[SQLQueryExecution]:
    query = db.query(SQLQueryExecution).filter(SQLQueryExecution.user_id == user_id)
    if chat_id is not None:
        query = query.filter(SQLQueryExecution.chat_id == chat_id)
    if connection_id is not None:
        query = query.filter(SQLQueryExecution.connection_id == connection_id)

    return query.order_by(SQLQueryExecution.execution_started_at.desc()).limit(limit).all()


def set_approval_status(
    db: Session,
    execution: SQLQueryExecution,
    *,
    approval_status: str,
) -> SQLQueryExecution:
    """Update approval status of an execution."""
    execution.approval_status = approval_status
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution
