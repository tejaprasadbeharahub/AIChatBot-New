from __future__ import annotations

import re

from app.schemas.nl_sql import TableMetadata

FORBIDDEN_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
    "grant",
    "revoke",
    "merge",
}

TABLE_PATTERN = re.compile(r"\b(?:from|join)\s+([a-zA-Z0-9_\.\"]+)", re.IGNORECASE)


def normalize_sql(sql: str) -> str:
    trimmed = (sql or "").strip()
    if trimmed.endswith(";"):
        trimmed = trimmed[:-1].strip()
    return trimmed


def ensure_read_only_sql(sql: str) -> None:
    normalized = normalize_sql(sql)
    if not normalized:
        raise ValueError("Generated SQL is empty")

    lowered = normalized.lower()
    first_keyword = lowered.split(None, 1)[0]
    if first_keyword not in {"select", "with"}:
        raise ValueError("Only read-only SELECT/CTE queries are allowed")

    if ";" in normalized:
        raise ValueError("Multiple SQL statements are not allowed")

    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{re.escape(keyword)}\b", lowered):
            raise ValueError(f"Blocked unsafe SQL keyword: {keyword.upper()}")


def extract_referenced_tables(sql: str) -> set[str]:
    refs: set[str] = set()
    for match in TABLE_PATTERN.finditer(sql):
        raw = match.group(1).strip('"').strip()
        refs.add(raw.split(".")[-1])
    return refs


def ensure_schema_consistency(sql: str, schema: list[TableMetadata]) -> None:
    known_tables = {item.table_name for item in schema}
    referenced_tables = extract_referenced_tables(sql)
    unknown_tables = sorted(ref for ref in referenced_tables if ref not in known_tables)
    if unknown_tables:
        raise ValueError(f"Generated SQL references unknown table(s): {', '.join(unknown_tables)}")
