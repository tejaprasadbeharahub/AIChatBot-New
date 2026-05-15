from __future__ import annotations

import re
from typing import Any

try:
    import sqlparse
except ImportError:  # pragma: no cover - optional parser dependency
    sqlparse = None

from app.models.db_connection import DBConnection
from app.schemas.nl_sql import TableMetadata
from app.services.sql.operation_classifier import (
    OperationRiskLevel,
    OperationType,
    assess_risk,
    classify_operation,
    requires_approval,
)


SUPPORTED_SQL_STARTS = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "CREATE",
    "ALTER",
    "DROP",
    "TRUNCATE",
    "WITH",
    "BEGIN",
    "START",
    "COMMIT",
    "ROLLBACK",
    "SAVEPOINT",
    "CALL",
    "EXEC",
    "EXECUTE",
)


def normalize_sql(sql: str) -> str:
    """Normalize SQL by removing trailing semicolon and extra whitespace."""
    return sql.strip().rstrip(";")


def is_read_only_operation(operation_type: OperationType) -> bool:
    """Check if operation is read-only (SELECT, WITH)."""
    return operation_type == OperationType.READ


def validate_sql_syntax(sql: str) -> None:
    """Validate SQL structure before deeper safety checks."""
    normalized = normalize_sql(sql)
    if not normalized:
        raise ValueError("SQL cannot be empty")

    if not normalized.upper().startswith(SUPPORTED_SQL_STARTS):
        raise ValueError(
            "Unsupported SQL operation. Query must start with one of: "
            + ", ".join(SUPPORTED_SQL_STARTS)
        )

    # Block chained statements early. This is intentional and conservative.
    if ";" in normalized:
        raise ValueError("Multiple SQL statements are not allowed")

    if sqlparse is not None:
        statements = [stmt for stmt in sqlparse.parse(normalized) if str(stmt).strip()]
        if len(statements) != 1:
            raise ValueError("Only a single SQL statement is allowed")

        stmt_type = statements[0].get_type()
        if stmt_type == "UNKNOWN":
            raise ValueError("SQL parser could not classify the statement")


def extract_referenced_tables(sql: str) -> set[str]:
    """Extract table names referenced in SQL query."""
    normalized = sql.upper()
    
    tables = set()
    
    # Remove comments
    normalized = re.sub(r"--.*?$", "", normalized, flags=re.MULTILINE)
    normalized = re.sub(r"/\*.*?\*/", "", normalized, flags=re.DOTALL)
    
    # FROM clause
    for match in re.finditer(r"\bFROM\s+([a-zA-Z0-9_\"'`]+(?:\s+[a-zA-Z0-9_]+)?)", normalized):
        table = match.group(1).strip().split()[0]
        tables.add(table.strip('"`"\''))
    
    # JOIN clauses
    for match in re.finditer(r"\b(?:INNER|LEFT|RIGHT|FULL|CROSS)?\s*JOIN\s+([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # INTO clause (INSERT)
    for match in re.finditer(r"\bINTO\s+([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # UPDATE clause
    for match in re.finditer(r"\bUPDATE\s+([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # DELETE FROM clause
    for match in re.finditer(r"\bDELETE\s+FROM\s+([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # CREATE TABLE
    for match in re.finditer(r"\bCREATE\s+(?:TEMPORARY|TEMP)?\s*TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # ALTER TABLE
    for match in re.finditer(r"\bALTER\s+TABLE\s+([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # DROP TABLE
    for match in re.finditer(r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    # TRUNCATE TABLE
    for match in re.finditer(r"\bTRUNCATE\s+(?:TABLE\s+)?([a-zA-Z0-9_\"'`]+)", normalized):
        table = match.group(1).strip()
        tables.add(table.strip('"`"\''))
    
    return tables


def extract_forbidden_patterns(sql: str) -> list[str]:
    """Check for forbidden SQL patterns that indicate injection or dangerous operations."""
    normalized = sql.upper()
    forbidden = []
    
    # Obvious injection patterns
    if any(pattern in normalized for pattern in ["'; DROP", "'; DELETE", "1' OR '1'='1", "' OR 1=1"]):
        forbidden.append("Potential SQL injection pattern detected")
    
    if re.search(r";\s*DROP\b", normalized):
        forbidden.append("Attempt to chain DROP via semicolon")
    
    if re.search(r";\s*DELETE\b", normalized):
        forbidden.append("Attempt to chain DELETE via semicolon")
    
    # EXEC/EXECUTE (potential code injection in SQL Server)
    if re.search(r"\b(EXEC|EXECUTE)\s*\(", normalized):
        forbidden.append("EXEC/EXECUTE not allowed - potential code injection")
    
    # xp_ stored procedures (SQL Server)
    if re.search(r"\bxp_\w+", normalized):
        forbidden.append("Extended stored procedures (xp_) not allowed")
    
    # sp_executesql
    if "SP_EXECUTESQL" in normalized:
        forbidden.append("Dynamic SQL execution (sp_executesql) not allowed")
    
    return forbidden


def ensure_schema_consistency(sql: str, schema: list[TableMetadata]) -> None:
    """Validate that referenced tables/columns exist in schema for existing tables."""
    if not schema:
        return
    
    operation_type = classify_operation(sql)
    
    # Only validate references for operations that read or modify existing tables
    if operation_type in (OperationType.READ, OperationType.INSERT, OperationType.UPDATE, OperationType.DELETE):
        referenced_tables = extract_referenced_tables(sql)
        schema_tables = {t.table_name.upper() for t in schema}
        
        for ref_table in referenced_tables:
            if ref_table.upper() not in schema_tables:
                raise ValueError(
                    f"Table '{ref_table}' not found in schema. "
                    f"Available tables: {', '.join(t.table_name for t in schema)}"
                )


def validate_sql_safety(
    sql: str,
    operation_type: OperationType | None = None,
    schema: list[TableMetadata] | None = None,
) -> tuple[OperationType, OperationRiskLevel, list[str]]:
    """
    Comprehensive SQL safety validation.
    
    Returns:
        (operation_type, risk_level, risk_messages)
    
    Raises:
        ValueError: If SQL contains forbidden patterns or fails validation.
    """
    normalized = normalize_sql(sql)
    
    # Validate syntax/shape before any classification or execution planning.
    validate_sql_syntax(normalized)

    # Classify operation
    if operation_type is None:
        operation_type = classify_operation(normalized)
    
    # Check for forbidden patterns
    forbidden = extract_forbidden_patterns(normalized)
    if forbidden:
        raise ValueError(f"SQL validation failed: {'; '.join(forbidden)}")
    
    # Assess risk
    risk_level, risk_messages = assess_risk(normalized, operation_type)
    
    # Validate schema consistency if provided
    if schema:
        ensure_schema_consistency(normalized, schema)
    
    return operation_type, risk_level, risk_messages
