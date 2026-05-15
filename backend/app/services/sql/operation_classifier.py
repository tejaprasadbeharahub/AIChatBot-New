from __future__ import annotations

import re
from enum import Enum


class OperationType(str, Enum):
    """Classified types of database operations."""
    READ = "read"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
    UPSERT = "upsert"
    SCHEMA_CREATE = "schema_create"
    SCHEMA_ALTER = "schema_alter"
    SCHEMA_DROP = "schema_drop"
    SCHEMA_INDEX = "schema_index"
    SCHEMA_VIEW = "schema_view"
    TRANSACTION = "transaction"
    ADMIN = "admin"
    UNKNOWN = "unknown"


class OperationRiskLevel(str, Enum):
    """Risk assessment for operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def classify_operation(sql: str) -> OperationType:
    """Classify SQL operation type from statement."""
    normalized = sql.strip().upper()
    
    # Remove leading comments
    normalized = re.sub(r"^(/\*.*?\*/|--|#).*?\n", "", normalized, flags=re.DOTALL)
    normalized = normalized.lstrip()
    
    # Detect operation type
    if re.match(r"^WITH\s+", normalized):
        # CTE - check what the main query is
        main_keyword = re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)\b", normalized)
        if main_keyword:
            return classify_operation(main_keyword.group(1))
        return OperationType.READ
    
    if re.match(r"^SELECT\b", normalized):
        return OperationType.READ
    
    if re.match(r"^INSERT\b", normalized):
        # Check if it's UPSERT pattern (INSERT ... ON CONFLICT / ON DUPLICATE)
        if re.search(r"\bON\s+(CONFLICT|DUPLICATE)", normalized):
            return OperationType.UPSERT
        return OperationType.INSERT

    if re.match(r"^MERGE\b", normalized):
        return OperationType.UPSERT
    
    if re.match(r"^UPDATE\b", normalized):
        return OperationType.UPDATE
    
    if re.match(r"^DELETE\b", normalized):
        return OperationType.DELETE
    
    if re.match(r"^CREATE\s+TABLE\b", normalized):
        return OperationType.SCHEMA_CREATE
    
    if re.match(r"^CREATE\s+(TEMPORARY|TEMP)\s+TABLE\b", normalized):
        return OperationType.SCHEMA_CREATE
    
    if re.match(r"^ALTER\s+TABLE\b", normalized):
        return OperationType.SCHEMA_ALTER
    
    if re.match(r"^DROP\s+TABLE\b", normalized):
        return OperationType.SCHEMA_DROP
    
    if re.match(r"^CREATE\s+INDEX\b", normalized):
        return OperationType.SCHEMA_INDEX
    
    if re.match(r"^DROP\s+INDEX\b", normalized):
        return OperationType.SCHEMA_INDEX
    
    if re.match(r"^CREATE\s+VIEW\b", normalized):
        return OperationType.SCHEMA_VIEW
    
    if re.match(r"^DROP\s+VIEW\b", normalized):
        return OperationType.SCHEMA_VIEW
    
    if re.match(r"^TRUNCATE\b", normalized):
        return OperationType.ADMIN
    
    if re.match(r"^(BEGIN|START|COMMIT|ROLLBACK|SAVEPOINT|RELEASE\s+SAVEPOINT)\b", normalized):
        return OperationType.TRANSACTION

    if re.match(r"^(CREATE|ALTER|DROP)\s+(PROCEDURE|PROC|FUNCTION)\b", normalized):
        return OperationType.ADMIN

    if re.match(r"^(CALL|EXEC|EXECUTE)\b", normalized):
        return OperationType.ADMIN
    
    if re.match(r"^(GRANT|REVOKE|ALTER\s+USER|CREATE\s+USER)\b", normalized):
        return OperationType.ADMIN
    
    return OperationType.UNKNOWN


def assess_risk(sql: str, operation_type: OperationType | None = None) -> tuple[OperationRiskLevel, list[str]]:
    """Assess risk level and identify dangerous patterns."""
    if operation_type is None:
        operation_type = classify_operation(sql)
    
    normalized = sql.strip().upper()
    risks: list[str] = []
    
    # DELETE without WHERE is critical
    if operation_type == OperationType.DELETE:
        if not re.search(r"\bWHERE\b", normalized):
            risks.append("DELETE without WHERE clause - affects ALL rows")
            return OperationRiskLevel.CRITICAL, risks
        if re.search(r"\bWHERE\s+1\s*=\s*1\b", normalized):
            risks.append("DELETE with WHERE 1=1 - affects ALL rows")
            return OperationRiskLevel.CRITICAL, risks
    
    # UPDATE without WHERE is critical
    if operation_type == OperationType.UPDATE:
        if not re.search(r"\bWHERE\b", normalized):
            risks.append("UPDATE without WHERE clause - affects ALL rows")
            return OperationRiskLevel.CRITICAL, risks
        if re.search(r"\bWHERE\s+1\s*=\s*1\b", normalized):
            risks.append("UPDATE with WHERE 1=1 - affects ALL rows")
            return OperationRiskLevel.CRITICAL, risks
    
    # TRUNCATE is high risk
    if operation_type == OperationType.ADMIN and "TRUNCATE" in normalized:
        risks.append("TRUNCATE - irreversibly removes ALL rows")
        return OperationRiskLevel.CRITICAL, risks
    
    # DROP TABLE is critical
    if operation_type == OperationType.SCHEMA_DROP:
        risks.append("DROP TABLE - irreversibly removes table and data")
        return OperationRiskLevel.CRITICAL, risks
    
    # ALTER TABLE is high risk
    if operation_type == OperationType.SCHEMA_ALTER:
        if re.search(r"\bDROP\b", normalized):
            risks.append("ALTER TABLE DROP - removes column irreversibly")
            return OperationRiskLevel.HIGH, risks
        if re.search(r"\bRENAME\b", normalized):
            risks.append("ALTER TABLE RENAME - may break application code")
            return OperationRiskLevel.MEDIUM, risks
        risks.append("ALTER TABLE - modifies schema structure")
        return OperationRiskLevel.MEDIUM, risks
    
    # CREATE TABLE is medium risk
    if operation_type == OperationType.SCHEMA_CREATE:
        risks.append("CREATE TABLE - adds new table to schema")
        return OperationRiskLevel.MEDIUM, risks
    
    # Bulk INSERT is medium risk
    if operation_type == OperationType.INSERT:
        insert_count = len(re.findall(r"\bVALUES\s*\(", normalized))
        if insert_count > 100:
            risks.append(f"Bulk INSERT with {insert_count}+ rows")
            return OperationRiskLevel.MEDIUM, risks
    
    # Schema view creation is low risk
    if operation_type == OperationType.SCHEMA_VIEW:
        return OperationRiskLevel.LOW, risks
    
    # Index operations are low risk
    if operation_type == OperationType.SCHEMA_INDEX:
        return OperationRiskLevel.LOW, risks
    
    # READ is low risk
    if operation_type == OperationType.READ:
        return OperationRiskLevel.LOW, risks
    
    return OperationRiskLevel.MEDIUM, risks


def requires_approval(operation_type: OperationType, risk_level: OperationRiskLevel) -> bool:
    """Determine if operation requires user approval before execution."""
    if risk_level in (OperationRiskLevel.CRITICAL, OperationRiskLevel.HIGH):
        return True
    if operation_type in (OperationType.SCHEMA_DROP, OperationType.SCHEMA_ALTER, OperationType.ADMIN):
        return True
    return False
