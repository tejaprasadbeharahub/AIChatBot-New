import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.sheet_datasource import SheetDatasource


def create(
    db: Session,
    *,
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    source_type: str,
    file_name: str | None = None,
    storage_path: str | None = None,
    file_size_bytes: int | None = None,
    sheet_url: str | None = None,
    sheet_id: str | None = None,
    sheet_tab: str | None = None,
) -> SheetDatasource:
    obj = SheetDatasource(
        chat_id=chat_id,
        user_id=user_id,
        source_type=source_type,
        file_name=file_name,
        storage_path=storage_path,
        file_size_bytes=file_size_bytes,
        sheet_url=sheet_url,
        sheet_id=sheet_id,
        sheet_tab=sheet_tab,
        status="pending",
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get(db: Session, datasource_id: uuid.UUID, user_id: uuid.UUID) -> SheetDatasource | None:
    return (
        db.query(SheetDatasource)
        .filter(SheetDatasource.id == datasource_id, SheetDatasource.user_id == user_id)
        .first()
    )


def list_for_chat(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID) -> list[SheetDatasource]:
    return (
        db.query(SheetDatasource)
        .filter(SheetDatasource.chat_id == chat_id, SheetDatasource.user_id == user_id)
        .order_by(SheetDatasource.created_at.desc())
        .all()
    )


def mark_ready(
    db: Session,
    obj: SheetDatasource,
    *,
    row_count: int,
    column_count: int,
    column_names_json: str,
    sheet_tabs_json: str | None = None,
) -> SheetDatasource:
    obj.status = "ready"
    obj.row_count = row_count
    obj.column_count = column_count
    obj.column_names = column_names_json
    obj.sheet_tabs = sheet_tabs_json
    obj.error_message = None
    obj.updated_at = datetime.now(timezone.utc)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def mark_failed(db: Session, obj: SheetDatasource, *, error_message: str) -> SheetDatasource:
    obj.status = "failed"
    obj.error_message = error_message
    obj.updated_at = datetime.now(timezone.utc)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete(db: Session, obj: SheetDatasource) -> None:
    db.delete(obj)
    db.commit()
