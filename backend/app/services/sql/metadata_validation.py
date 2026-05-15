"""Centralized metadata validation and normalization utilities.

Ensures consistent, type-safe access to schema metadata across all services
and database providers (PostgreSQL, MySQL, SQL Server, SQLite).
"""

from __future__ import annotations

import logging
from typing import Any

from app.models.db_connection import DBConnection
from app.schemas.nl_sql import ColumnMetadata, RelationshipMetadata, TableMetadata


logger = logging.getLogger(__name__)


class MetadataValidationError(Exception):
    """Raised when metadata validation fails."""

    pass


def validate_column_metadata(column: ColumnMetadata) -> None:
    """Validate a single column metadata object."""
    if not column.name or not isinstance(column.name, str):
        raise MetadataValidationError(f"Invalid column name: {column.name}")
    if not column.data_type or not isinstance(column.data_type, str):
        raise MetadataValidationError(
            f"Column '{column.name}' has invalid data_type: {column.data_type}"
        )
    if not isinstance(column.nullable, bool):
        raise MetadataValidationError(
            f"Column '{column.name}' has invalid nullable flag: {column.nullable}"
        )


def validate_relationship_metadata(rel: RelationshipMetadata, table_name: str) -> None:
    """Validate a single relationship metadata object."""
    if not rel.constrained_columns or not isinstance(rel.constrained_columns, list):
        raise MetadataValidationError(
            f"Table '{table_name}': invalid constrained_columns in FK: {rel.constrained_columns}"
        )
    if not rel.referred_columns or not isinstance(rel.referred_columns, list):
        raise MetadataValidationError(
            f"Table '{table_name}': invalid referred_columns in FK: {rel.referred_columns}"
        )
    # referred_table can be None for some databases
    if rel.referred_table is not None and not isinstance(rel.referred_table, str):
        raise MetadataValidationError(
            f"Table '{table_name}': invalid referred_table: {rel.referred_table}"
        )


def validate_table_metadata(table: TableMetadata) -> None:
    """Validate a single table metadata object.
    
    Raises MetadataValidationError if any required field is invalid.
    """
    if not table.table_name or not isinstance(table.table_name, str):
        raise MetadataValidationError(f"Invalid table_name: {table.table_name}")
    
    if not isinstance(table.columns, list):
        raise MetadataValidationError(
            f"Table '{table.table_name}' has invalid columns field (expected list)"
        )
    
    if not isinstance(table.relationships, list):
        raise MetadataValidationError(
            f"Table '{table.table_name}' has invalid relationships field (expected list)"
        )
    
    # Validate each column
    for col in table.columns:
        try:
            validate_column_metadata(col)
        except MetadataValidationError as e:
            raise MetadataValidationError(
                f"Table '{table.table_name}': {str(e)}"
            ) from e
    
    # Validate each relationship
    for rel in table.relationships:
        try:
            validate_relationship_metadata(rel, table.table_name)
        except MetadataValidationError as e:
            raise MetadataValidationError(
                f"Table '{table.table_name}': {str(e)}"
            ) from e


def validate_schema_metadata(schema: list[TableMetadata]) -> None:
    """Validate entire schema metadata collection.
    
    Raises MetadataValidationError if any table is invalid.
    """
    if not isinstance(schema, list):
        raise MetadataValidationError("Schema must be a list of TableMetadata objects")
    
    if not schema:
        logger.warning("Schema metadata is empty")
        return
    
    table_names = set()
    for table in schema:
        if not isinstance(table, TableMetadata):
            raise MetadataValidationError(
                f"Expected TableMetadata object, got {type(table).__name__}"
            )
        
        try:
            validate_table_metadata(table)
        except MetadataValidationError as e:
            raise e
        
        # Check for duplicate table names
        if table.table_name in table_names:
            raise MetadataValidationError(
                f"Duplicate table name in schema: {table.table_name}"
            )
        table_names.add(table.table_name)


def get_table_name(table: TableMetadata) -> str:
    """Safely get table name from metadata with validation."""
    if not isinstance(table, TableMetadata):
        raise MetadataValidationError(
            f"Expected TableMetadata, got {type(table).__name__}"
        )
    if not table.table_name:
        raise MetadataValidationError("TableMetadata has no table_name")
    return table.table_name


def get_column_name(column: ColumnMetadata) -> str:
    """Safely get column name from metadata with validation."""
    if not isinstance(column, ColumnMetadata):
        raise MetadataValidationError(
            f"Expected ColumnMetadata, got {type(column).__name__}"
        )
    if not column.name:
        raise MetadataValidationError("ColumnMetadata has no name")
    return column.name


def get_table_columns(table: TableMetadata) -> list[ColumnMetadata]:
    """Safely get columns from table metadata with validation."""
    table_name = get_table_name(table)
    if not isinstance(table.columns, list):
        raise MetadataValidationError(
            f"Table '{table_name}' columns field is not a list"
        )
    return table.columns


def get_table_relationships(table: TableMetadata) -> list[RelationshipMetadata]:
    """Safely get relationships from table metadata with validation."""
    table_name = get_table_name(table)
    if not isinstance(table.relationships, list):
        raise MetadataValidationError(
            f"Table '{table_name}' relationships field is not a list"
        )
    return table.relationships


def get_table_names_from_schema(schema: list[TableMetadata]) -> list[str]:
    """Extract all table names from schema with validation."""
    if not isinstance(schema, list):
        raise MetadataValidationError("Schema must be a list")
    
    table_names = []
    for table in schema:
        try:
            table_names.append(get_table_name(table))
        except MetadataValidationError as e:
            logger.error(f"Invalid table in schema: {e}")
            raise
    return table_names


def find_table_in_schema(
    schema: list[TableMetadata], table_name: str
) -> TableMetadata | None:
    """Find a table by name in schema (case-insensitive)."""
    if not isinstance(schema, list):
        raise MetadataValidationError("Schema must be a list")
    
    table_name_upper = table_name.upper()
    for table in schema:
        try:
            if get_table_name(table).upper() == table_name_upper:
                return table
        except MetadataValidationError as e:
            logger.debug(f"Skipping invalid table: {e}")
            continue
    return None


def find_column_in_table(
    table: TableMetadata, column_name: str
) -> ColumnMetadata | None:
    """Find a column by name in table (case-insensitive)."""
    table_name = get_table_name(table)
    column_name_upper = column_name.upper()
    
    try:
        columns = get_table_columns(table)
        for col in columns:
            if get_column_name(col).upper() == column_name_upper:
                return col
    except MetadataValidationError as e:
        logger.debug(f"Error searching columns in table '{table_name}': {e}")
    
    return None


def schema_to_dict(schema: list[TableMetadata]) -> dict[str, Any]:
    """Convert schema metadata to dict representation for debugging/logging."""
    result = {}
    for table in schema:
        try:
            table_name = get_table_name(table)
            result[table_name] = {
                "columns": [
                    {
                        "name": col.name,
                        "type": col.data_type,
                        "nullable": col.nullable,
                    }
                    for col in get_table_columns(table)
                ],
                "relationships": [
                    {
                        "from": rel.constrained_columns,
                        "to_table": rel.referred_table,
                        "to_columns": rel.referred_columns,
                    }
                    for rel in get_table_relationships(table)
                ],
            }
        except MetadataValidationError as e:
            logger.warning(f"Error converting table to dict: {e}")
            continue
    return result


def log_schema_metadata(schema: list[TableMetadata], label: str = "Schema") -> None:
    """Log schema metadata for debugging purposes."""
    try:
        validate_schema_metadata(schema)
        schema_dict = schema_to_dict(schema)
        logger.debug(f"{label}: {schema_dict}")
    except MetadataValidationError as e:
        logger.error(f"Invalid schema metadata: {e}")
