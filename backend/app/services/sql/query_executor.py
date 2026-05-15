from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from datetime import date, datetime, time as dt_time
from typing import Any

from sqlalchemy import text

from app.core.config import settings
from app.models.db_connection import DBConnection
from app.services.sql.connection_manager import get_provider_connection
from app.services.sql.operation_classifier import OperationType, classify_operation
from app.services.sql.sql_guard import normalize_sql


logger = logging.getLogger(__name__)


def _to_json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, (datetime, date, dt_time)):
        return value.isoformat()
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_to_json_safe(item) for item in value]
    return str(value)


def _apply_provider_timeout(connection: DBConnection, conn, timeout_seconds: int) -> None:
    timeout_ms = max(timeout_seconds, 1) * 1000
    provider = connection.provider

    if provider == "postgresql":
        conn.execute(text("SET statement_timeout = :timeout_ms"), {"timeout_ms": timeout_ms})
    elif provider == "mysql":
        conn.execute(text("SET SESSION MAX_EXECUTION_TIME = :timeout_ms"), {"timeout_ms": timeout_ms})
    elif provider == "sqlserver":
        conn.execute(text("SET LOCK_TIMEOUT :timeout_ms"), {"timeout_ms": timeout_ms})


@contextmanager
def _transaction_scope(conn):
    """
    Centralized transaction management for provider connections.

    - Reuses an existing transaction when already active (prevents nested begin conflicts).
    - Starts/commits/rolls back a new transaction when no transaction is active.
    """
    if conn.in_transaction():
        logger.debug("Reusing existing active transaction on connection")
        yield
        return

    logger.debug("Starting new transaction on connection")
    with conn.begin():
        yield


def execute_read_only_query(
    *,
    connection: DBConnection,
    sql: str,
    max_rows: int,
) -> tuple[list[str], list[dict[str, Any]], int, int]:
    normalized = normalize_sql(sql)
    effective_limit = min(max_rows, settings.sql_max_row_limit)

    if connection.provider == "sqlserver":
        wrapped_sql = (
            f"SELECT TOP {effective_limit} * FROM (\n"
            f"{normalized}\n"
            ") AS nl_sql_subquery"
        )
        params: dict[str, Any] = {}
    else:
        wrapped_sql = (
            "SELECT * FROM (\n"
            f"{normalized}\n"
            ") AS nl_sql_subquery LIMIT :_max_rows"
        )
        params = {"_max_rows": effective_limit}

    started_at = time.perf_counter()
    with get_provider_connection(connection) as conn:
        _apply_provider_timeout(connection, conn, settings.sql_query_timeout_seconds)
        result = conn.execute(text(wrapped_sql), params)
        rows = result.fetchall()
        columns = list(result.keys())

    duration_ms = int((time.perf_counter() - started_at) * 1000)

    formatted_rows: list[dict[str, Any]] = []
    for row in rows:
        item = {}
        for col in columns:
            value = row._mapping.get(col)
            item[col] = _to_json_safe(value)
        formatted_rows.append(item)

    return columns, formatted_rows, len(formatted_rows), duration_ms


def execute_sql_query(
    *,
    connection: DBConnection,
    sql: str,
    max_rows: int,
) -> tuple[list[str], list[dict[str, Any]], int, int]:
    """
    Execute SQL safely based on operation type.

    READ operations are wrapped/limited for bounded result size.
    Non-READ operations are executed directly without subquery wrapping.
    """
    normalized = normalize_sql(sql)
    operation_type = classify_operation(normalized)

    if operation_type == OperationType.READ:
        return execute_read_only_query(connection=connection, sql=normalized, max_rows=max_rows)

    started_at = time.perf_counter()
    try:
        with get_provider_connection(connection) as conn:
            with _transaction_scope(conn):
                _apply_provider_timeout(connection, conn, settings.sql_query_timeout_seconds)
                result = conn.execute(text(normalized))
    except Exception as exc:
        logger.exception("SQL execution failed; transaction rolled back")
        raise

    duration_ms = int((time.perf_counter() - started_at) * 1000)
    affected_rows = result.rowcount if result.rowcount is not None and result.rowcount > -1 else 0

    return [], [], affected_rows, duration_ms
