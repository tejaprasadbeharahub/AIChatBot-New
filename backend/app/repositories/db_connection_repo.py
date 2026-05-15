import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.db_connection import DBConnection


def list_connections_for_user(db: Session, user_id: uuid.UUID) -> list[DBConnection]:
    return (
        db.query(DBConnection)
        .filter(DBConnection.user_id == user_id)
        .order_by(DBConnection.updated_at.desc())
        .all()
    )


def get_connection_for_user(db: Session, connection_id: uuid.UUID, user_id: uuid.UUID) -> DBConnection | None:
    return (
        db.query(DBConnection)
        .filter(DBConnection.id == connection_id, DBConnection.user_id == user_id)
        .first()
    )


def create_connection(
    db: Session,
    *,
    user_id: uuid.UUID,
    name: str,
    provider: str,
    host: str | None,
    port: int | None,
    database_name: str | None,
    username: str | None,
    encrypted_password: str | None,
    sqlite_path: str | None,
    extra_options: dict | None,
) -> DBConnection:
    conn = DBConnection(
        user_id=user_id,
        name=name.strip(),
        provider=provider,
        host=host,
        port=port,
        database_name=database_name,
        username=username,
        encrypted_password=encrypted_password,
        sqlite_path=sqlite_path,
        extra_options=extra_options or {},
    )
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def update_connection(db: Session, conn: DBConnection, **updates: object) -> DBConnection:
    for key, value in updates.items():
        if hasattr(conn, key):
            setattr(conn, key, value)

    conn.updated_at = datetime.now(timezone.utc)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def mark_validated(db: Session, conn: DBConnection) -> DBConnection:
    conn.last_validated_at = datetime.now(timezone.utc)
    conn.updated_at = datetime.now(timezone.utc)
    db.add(conn)
    db.commit()
    db.refresh(conn)
    return conn


def delete_connection(db: Session, conn: DBConnection) -> None:
    db.delete(conn)
    db.commit()
