from __future__ import annotations

import logging

from sqlalchemy import inspect

from app.models.db_connection import DBConnection
from app.schemas.nl_sql import ColumnMetadata, RelationshipMetadata, TableMetadata
from app.services.sql.connection_manager import create_provider_engine


logger = logging.getLogger(__name__)


def discover_schema(connection: DBConnection) -> list[TableMetadata]:
    """Discover database schema from connected database.
    
    Returns a list of TableMetadata objects normalized across all database providers.
    
    Raises:
        Exception: If schema discovery fails.
    """
    engine = create_provider_engine(connection)
    try:
        inspector = inspect(engine)
        table_names = sorted(inspector.get_table_names())
        logger.debug(f"Discovered {len(table_names)} tables from {connection.provider} database")
        
        tables: list[TableMetadata] = []

        for table_name in table_names:
            try:
                raw_columns = inspector.get_columns(table_name)
                columns = [
                    ColumnMetadata(
                        name=str(col.get("name")).strip(),
                        data_type=str(col.get("type")).strip(),
                        nullable=bool(col.get("nullable", True)),
                    )
                    for col in raw_columns
                ]

                raw_fks = inspector.get_foreign_keys(table_name)
                relationships = [
                    RelationshipMetadata(
                        constrained_columns=[str(item).strip() for item in fk.get("constrained_columns") or []],
                        referred_table=str(fk.get("referred_table")).strip() if fk.get("referred_table") else None,
                        referred_columns=[str(item).strip() for item in fk.get("referred_columns") or []],
                    )
                    for fk in raw_fks
                ]

                table = TableMetadata(
                    table_name=table_name.strip(),
                    columns=columns,
                    relationships=relationships,
                )
                
                logger.debug(
                    f"Discovered table '{table_name}' with {len(columns)} columns and {len(relationships)} foreign keys"
                )
                tables.append(table)
            except Exception as e:
                logger.warning(f"Error discovering metadata for table '{table_name}': {e}")
                # Continue with other tables instead of failing entirely
                continue

        return tables
    finally:
        engine.dispose()


def build_schema_text(schema: list[TableMetadata]) -> str:
    lines: list[str] = []
    for table in schema:
        lines.append(f"Table: {table.table_name}")
        for column in table.columns:
            nullable = "NULL" if column.nullable else "NOT NULL"
            lines.append(f"  - {column.name} ({column.data_type}, {nullable})")
        for rel in table.relationships:
            src_cols = ", ".join(rel.constrained_columns) or "(unknown)"
            ref_cols = ", ".join(rel.referred_columns) or "(unknown)"
            lines.append(f"  FK: {src_cols} -> {rel.referred_table}({ref_cols})")
    return "\n".join(lines)
