"""Lightweight JSON-schema-like validation for MCP tool arguments/results."""

from __future__ import annotations

from typing import Any


class SchemaValidationError(ValueError):
    """Raised when data does not satisfy the provided schema."""


def _assert_type(path: str, value: Any, expected: str) -> None:
    type_map = {
        "object": dict,
        "array": list,
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "null": type(None),
    }

    py_type = type_map.get(expected)
    if py_type is None:
        # Unknown type declaration: accept to avoid over-restricting third-party schemas.
        return

    if expected == "integer" and isinstance(value, bool):
        raise SchemaValidationError(f"{path}: expected integer, got boolean")

    if not isinstance(value, py_type):
        raise SchemaValidationError(f"{path}: expected {expected}, got {type(value).__name__}")


def validate_against_schema(data: Any, schema: dict[str, Any] | None, path: str = "$") -> None:
    """Validate data against a subset of JSON Schema used by MCP tools."""
    if not schema:
        return

    schema_type = schema.get("type")
    if schema_type:
        _assert_type(path, data, str(schema_type))

    if schema_type == "object" and isinstance(data, dict):
        required = schema.get("required", []) or []
        for key in required:
            if key not in data:
                raise SchemaValidationError(f"{path}: missing required property '{key}'")

        props = schema.get("properties", {}) or {}
        for key, value in data.items():
            child_schema = props.get(key)
            if child_schema:
                validate_against_schema(value, child_schema, f"{path}.{key}")

    if schema_type == "array" and isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema:
            for i, item in enumerate(data):
                validate_against_schema(item, item_schema, f"{path}[{i}]")
