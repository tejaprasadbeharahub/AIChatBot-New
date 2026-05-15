from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.repositories import db_connection_repo, sql_query_execution_repo
from app.repositories.chat_repo import get_chat_for_user
from app.repositories.message_repo import create_message
from app.schemas.nl_sql import DBConnectionCreate, DBConnectionRead, DBConnectionUpdate
from app.services.chat_memory_service import get_thread_memory
from app.services.chat_thread_service import create_chat as create_chat_thread
from app.services.sql.connection_manager import ping_connection
from app.services.sql.nl_sql_generator import generate_sql_from_question
from app.services.sql.query_executor import execute_sql_query
from app.services.sql.schema_discovery import discover_schema
from app.services.sql.security import encrypt_secret
from app.services.sql.approval_workflow import (
    OperationApprovalRequest,
    determine_requires_approval,
    create_approval_request,
)
from app.services.sql.sql_guard_enhanced import validate_sql_safety, normalize_sql
from app.services.sql.metadata_validation import (
    validate_schema_metadata,
    MetadataValidationError,
    log_schema_metadata,
)


logger = logging.getLogger(__name__)


class NLSQLExecutionError(Exception):
    pass


def _to_connection_read(item) -> DBConnectionRead:
    return DBConnectionRead(
        id=item.id,
        user_id=item.user_id,
        name=item.name,
        provider=item.provider,
        host=item.host,
        port=item.port,
        database_name=item.database_name,
        username=item.username,
        sqlite_path=item.sqlite_path,
        extra_options=item.extra_options or {},
        is_active=item.is_active,
        has_password=bool(item.encrypted_password),
        last_validated_at=item.last_validated_at,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


def list_connections(db: Session, user_id: uuid.UUID) -> list[DBConnectionRead]:
    return [_to_connection_read(item) for item in db_connection_repo.list_connections_for_user(db, user_id)]


def create_connection(db: Session, user: User, payload: DBConnectionCreate) -> DBConnectionRead:
    encrypted_password = encrypt_secret(payload.password) if payload.password else None
    conn = db_connection_repo.create_connection(
        db,
        user_id=user.id,
        name=payload.name,
        provider=payload.provider,
        host=payload.host,
        port=payload.port,
        database_name=payload.database_name,
        username=payload.username,
        encrypted_password=encrypted_password,
        sqlite_path=payload.sqlite_path,
        extra_options=payload.extra_options,
    )
    return _to_connection_read(conn)


def update_connection(db: Session, user_id: uuid.UUID, connection_id: uuid.UUID, payload: DBConnectionUpdate) -> DBConnectionRead:
    conn = db_connection_repo.get_connection_for_user(db, connection_id, user_id)
    if conn is None:
        raise ValueError("Connection not found")

    updates: dict[str, object] = {}
    for field in ["name", "host", "port", "database_name", "username", "sqlite_path", "extra_options", "is_active"]:
        value = getattr(payload, field)
        if value is not None:
            updates[field] = value

    if payload.password is not None:
        updates["encrypted_password"] = encrypt_secret(payload.password) if payload.password else None

    updated = db_connection_repo.update_connection(db, conn, **updates)
    return _to_connection_read(updated)


def delete_connection(db: Session, user_id: uuid.UUID, connection_id: uuid.UUID) -> None:
    conn = db_connection_repo.get_connection_for_user(db, connection_id, user_id)
    if conn is None:
        raise ValueError("Connection not found")
    db_connection_repo.delete_connection(db, conn)


def test_connection(db: Session, user_id: uuid.UUID, connection_id: uuid.UUID) -> tuple[bool, str]:
    conn = db_connection_repo.get_connection_for_user(db, connection_id, user_id)
    if conn is None:
        raise ValueError("Connection not found")

    try:
        ping_connection(conn)
        db_connection_repo.mark_validated(db, conn)
        return True, "Connection validated successfully"
    except Exception as exc:
        return False, f"Connection failed: {exc}"


def build_schema_metadata(db: Session, user_id: uuid.UUID, connection_id: uuid.UUID):
    conn = db_connection_repo.get_connection_for_user(db, connection_id, user_id)
    if conn is None:
        raise ValueError("Connection not found")
    
    try:
        schema = discover_schema(conn)
        validate_schema_metadata(schema)
        log_schema_metadata(schema, f"Schema for connection {connection_id}")
        return schema
    except MetadataValidationError as e:
        raise ValueError(f"Schema metadata error: {e}") from e
    except Exception as e:
        logger.exception(f"Error discovering schema for connection {connection_id}")
        raise ValueError(f"Failed to discover database schema: {e}") from e


def list_query_history(
    db: Session,
    *,
    user_id: uuid.UUID,
    chat_id: uuid.UUID | None,
    connection_id: uuid.UUID | None,
    limit: int,
):
    return sql_query_execution_repo.list_history_for_user(
        db,
        user_id=user_id,
        chat_id=chat_id,
        connection_id=connection_id,
        limit=limit,
    )


def execute_nl_query(
    db: Session,
    *,
    user: User,
    connection_id: uuid.UUID,
    question: str,
    chat_id: uuid.UUID | None,
    max_rows: int | None,
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID, str, object, OperationApprovalRequest | None]:
    """
    Execute a natural language query with smart operation classification and approval workflow.
    
    Returns:
        (chat_id, user_message_id, assistant_message_id, reply, execution, approval_request_if_pending)
    """
    conn = db_connection_repo.get_connection_for_user(db, connection_id, user.id)
    if conn is None:
        raise ValueError("Connection not found")

    if chat_id is not None:
        chat = get_chat_for_user(db, chat_id, user.id)
        if chat is None:
            raise ValueError("Chat not found")
    else:
        chat = create_chat_thread(db, user.id)

    normalized_question = question.strip()
    if not normalized_question:
        raise ValueError("Question cannot be empty")

    # Save user message
    user_message = create_message(db, chat.id, "user", normalized_question)

    # Discover schema with defensive validation
    try:
        schema = discover_schema(conn)
        validate_schema_metadata(schema)
        log_schema_metadata(schema, f"Schema for connection {connection_id}")
    except MetadataValidationError as e:
        raise ValueError(f"Schema metadata error: {e}") from e
    except Exception as e:
        logger.exception(f"Unexpected error discovering schema for connection {connection_id}")
        raise ValueError(f"Failed to discover database schema: {e}") from e
    
    # Get conversation history
    # Get conversation history
    history = get_thread_memory(db, chat_id=chat.id, max_turns=settings.chat_memory_turns)

    # Generate SQL from natural language with validation
    try:
        ai_response = generate_sql_from_question(
            question=normalized_question,
            schema=schema,
            history=history,
        )
    except ValueError as e:
        # AI failed to generate valid SQL (refusal, explanation, malformed, etc.)
        logger.warning(f"AI SQL generation failed: {e}")
        error_reply = f"❌ Unable to generate valid SQL: {str(e)}\n\nPlease rephrase your question or try a different approach."
        
        assistant_message = create_message(db, chat.id, "assistant", error_reply)
        db.commit()
        
        # Create a failed execution record
        execution = sql_query_execution_repo.create_execution(
            db,
            connection_id=conn.id,
            user_id=user.id,
            chat_id=chat.id,
            message_id=assistant_message.id,
            user_question=normalized_question,
            generated_sql="",
            sql_explanation=None,
            operation_type="unknown",
            risk_level="high",
            risk_messages=["AI generation failed"],
        )
        
        # Mark as failed
        execution = sql_query_execution_repo.mark_failure(
            db,
            execution,
            duration_ms=0,
            error_message=f"AI generation failed: {str(e)}",
        )
        
        raise NLSQLExecutionError(error_reply) from e
    except Exception as e:
        logger.exception("Unexpected error during SQL generation")
        error_reply = "❌ An unexpected error occurred during SQL generation. Please try again."
        
        assistant_message = create_message(db, chat.id, "assistant", error_reply)
        db.commit()
        
        raise NLSQLExecutionError(error_reply) from e
    
    sql = normalize_sql(ai_response.sql)
    explanation = ai_response.explanation
    operation_type = ai_response.operation_type
    warnings = ai_response.warnings

    # Validate SQL safety and assess risk
    operation_type, risk_level, risk_messages = validate_sql_safety(sql, schema=schema)
    
    # Combine AI warnings with safety check warnings
    all_warnings = list(set(warnings + risk_messages))

    # Create execution record with operation type and risk info
    assistant_message = create_message(
        db, 
        chat.id, 
        "assistant", 
        f"Generated SQL for {operation_type} operation. "
        f"Risk level: {risk_level}. Awaiting approval..." if determine_requires_approval(operation_type, risk_level) 
        else f"Generated SQL for {operation_type} operation..."
    )

    execution = sql_query_execution_repo.create_execution(
        db,
        connection_id=conn.id,
        user_id=user.id,
        chat_id=chat.id,
        message_id=assistant_message.id,
        user_question=normalized_question,
        generated_sql=sql,
        sql_explanation=explanation,
        operation_type=operation_type,
        risk_level=risk_level,
        risk_messages=all_warnings,
    )

    # Check if approval is required
    approval_needed = determine_requires_approval(operation_type, risk_level)
    
    if approval_needed:
        # Create approval request
        approval_request = OperationApprovalRequest(
            execution_id=execution.id,
            operation_type=operation_type,
            risk_level=risk_level,
            risk_messages=all_warnings,
            generated_sql=sql,
            sql_explanation=explanation,
            question=normalized_question,
        )
        
        # Mark execution as pending approval
        execution = sql_query_execution_repo.set_approval_status(
            db, execution, approval_status="pending"
        )
        
        reply = f"⚠️ Operation requires approval before execution.\n\n"
        reply += f"**Operation Type:** {operation_type}\n"
        reply += f"**Risk Level:** {risk_level.upper()}\n"
        if all_warnings:
            reply += f"**Risks:** {'; '.join(all_warnings)}\n\n"
        reply += f"Generated SQL:\n```sql\n{sql}\n```"
        
        assistant_message.content = reply
        db.add(assistant_message)
        db.commit()
        
        return chat.id, user_message.id, assistant_message.id, reply, execution, approval_request
    
    # Auto-approved low-risk operations - proceed with execution
    execution = sql_query_execution_repo.set_approval_status(
        db, execution, approval_status="auto_approved"
    )

    try:
        effective_max_rows = max_rows or settings.sql_default_row_limit
        columns, rows, row_count, duration_ms = execute_sql_query(
            connection=conn,
            sql=sql,
            max_rows=effective_max_rows,
        )
        execution = sql_query_execution_repo.mark_success(
            db,
            execution,
            duration_ms=duration_ms,
            row_count=row_count,
            returned_columns=columns,
            result_rows=rows,
        )

        assistant_text = (
            f"✅ Query executed successfully!\n\n"
            f"**Operation:** {operation_type}\n"
            f"**Duration:** {duration_ms}ms\n"
            f"**Rows returned:** {row_count}"
        )
        assistant_message.content = assistant_text
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        return chat.id, user_message.id, assistant_message.id, assistant_text, execution, None
    except Exception as exc:
        db.rollback()
        error_text = str(exc)
        execution = sql_query_execution_repo.mark_failure(
            db,
            execution,
            duration_ms=0,
            error_message=error_text,
        )
        failure_reply = f"❌ Query execution failed: {error_text}"
        assistant_message.content = failure_reply
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        raise NLSQLExecutionError(error_text) from exc
