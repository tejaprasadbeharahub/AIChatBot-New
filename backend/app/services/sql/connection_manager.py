from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from app.models.db_connection import DBConnection
from app.services.sql.security import decrypt_secret


def build_sqlalchemy_url(connection: DBConnection) -> str:
    provider = connection.provider
    options = connection.extra_options or {}

    if provider == "sqlite":
        sqlite_path = (connection.sqlite_path or "").strip()
        if not sqlite_path:
            raise ValueError("SQLite connection requires sqlite_path")

        if sqlite_path == ":memory:":
            return "sqlite+pysqlite:///:memory:"

        resolved = Path(sqlite_path).expanduser().resolve()
        return f"sqlite+pysqlite:///{resolved.as_posix()}"

    host = (connection.host or "").strip()
    db_name = (connection.database_name or "").strip()
    username = (connection.username or "").strip()
    password = decrypt_secret(connection.encrypted_password) or ""
    port = connection.port

    if not host or not db_name or not username:
        raise ValueError("Connection is missing host, database_name, or username")

    encoded_user = quote_plus(username)
    encoded_password = quote_plus(password)

    if provider == "postgresql":
        resolved_port = port or 5432
        return f"postgresql+psycopg2://{encoded_user}:{encoded_password}@{host}:{resolved_port}/{db_name}"

    if provider == "mysql":
        resolved_port = port or 3306
        return f"mysql+pymysql://{encoded_user}:{encoded_password}@{host}:{resolved_port}/{db_name}"

    if provider == "sqlserver":
        resolved_port = port or 1433
        driver = quote_plus(str(options.get("driver") or "ODBC Driver 18 for SQL Server"))
        trust_server_certificate = str(options.get("trust_server_certificate", "yes")).lower()
        return (
            f"mssql+pyodbc://{encoded_user}:{encoded_password}@{host}:{resolved_port}/{db_name}"
            f"?driver={driver}&TrustServerCertificate={trust_server_certificate}"
        )

    raise ValueError(f"Unsupported provider: {provider}")


def _connect_args(connection: DBConnection) -> dict:
    if connection.provider == "sqlite":
        return {"check_same_thread": False}
    return {}


def create_provider_engine(connection: DBConnection) -> Engine:
    return create_engine(
        build_sqlalchemy_url(connection),
        pool_pre_ping=True,
        future=True,
        connect_args=_connect_args(connection),
    )


@contextmanager
def get_provider_connection(connection: DBConnection):
    engine = create_provider_engine(connection)
    try:
        with engine.connect() as conn:
            yield conn
    finally:
        engine.dispose()


def ping_connection(connection: DBConnection) -> None:
    with get_provider_connection(connection) as conn:
        conn.execute(text("SELECT 1"))
