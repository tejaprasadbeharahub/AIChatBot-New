"""
Sheet Agent Service — orchestrates file storage, metadata extraction, and NL querying.
"""

import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sheet_datasource import SheetDatasource
from app.models.user import User
from app.repositories import sheet_datasource_repo
from app.repositories.chat_repo import get_chat_for_user
from app.services.sheet_agent.file_loader import (
    build_datasource_metadata,
    load_dataframe,
)
from app.services.sheet_agent.sheets_connector import (
    build_google_sheet_metadata,
    load_google_sheet,
)
from app.services.sheet_agent.agent import run_sheet_query


_ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
_MAX_FILE_MB = 50


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_sheet_file(file: UploadFile) -> None:
    """Raise HTTPException if the uploaded file is not a supported type or too large."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Uploaded file has no name.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Allowed: {sorted(_ALLOWED_EXTENSIONS)}",
        )


def _get_sheet_upload_dir() -> Path:
    base = settings.upload_dir or "./uploads"
    path = Path(base)
    if not path.is_absolute():
        from app.services.attachment_service import PROJECT_ROOT
        path = (PROJECT_ROOT / path).resolve()
    sheet_dir = path / "sheets"
    sheet_dir.mkdir(parents=True, exist_ok=True)
    return sheet_dir


# ---------------------------------------------------------------------------
# Upload CSV/XLSX
# ---------------------------------------------------------------------------

async def upload_sheet_file(
    db: Session,
    *,
    file: UploadFile,
    chat_id: uuid.UUID,
    user: User,
) -> SheetDatasource:
    """Store an uploaded CSV/XLSX file and record it in the database."""
    chat = get_chat_for_user(db, chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    validate_sheet_file(file)

    content = await file.read()
    file_size = len(content)

    max_bytes = _MAX_FILE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {_MAX_FILE_MB} MB limit.",
        )

    # Persist to disk
    suffix = Path(file.filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{suffix}"
    storage_path = _get_sheet_upload_dir() / unique_name
    storage_path.write_bytes(content)

    source_type = "xlsx" if suffix in {".xlsx", ".xls"} else "csv"

    # Create DB record (status=pending)
    datasource = sheet_datasource_repo.create(
        db,
        chat_id=chat_id,
        user_id=user.id,
        source_type=source_type,
        file_name=file.filename,
        storage_path=str(storage_path),
        file_size_bytes=file_size,
    )

    # Populate metadata inline (files are small enough)
    try:
        meta = build_datasource_metadata(str(storage_path))
        datasource = sheet_datasource_repo.mark_ready(
            db,
            datasource,
            row_count=meta["row_count"],
            column_count=meta["column_count"],
            column_names_json=meta["column_names_json"],
            sheet_tabs_json=meta["sheet_tabs_json"],
        )
    except HTTPException as exc:
        sheet_datasource_repo.mark_failed(db, datasource, error_message=exc.detail)
        raise
    except Exception as exc:
        sheet_datasource_repo.mark_failed(db, datasource, error_message=str(exc))
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {exc}") from exc

    return datasource


# ---------------------------------------------------------------------------
# Connect Google Sheet
# ---------------------------------------------------------------------------

def connect_google_sheet(
    db: Session,
    *,
    chat_id: uuid.UUID,
    user: User,
    sheet_url: str,
    sheet_tab: Optional[str] = None,
) -> SheetDatasource:
    """Validate and record a Google Sheets connection."""
    chat = get_chat_for_user(db, chat_id, user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    # Create DB record (status=pending)
    datasource = sheet_datasource_repo.create(
        db,
        chat_id=chat_id,
        user_id=user.id,
        source_type="google_sheets",
        sheet_url=sheet_url,
        sheet_tab=sheet_tab,
    )

    try:
        meta = build_google_sheet_metadata(sheet_url, sheet_tab=sheet_tab)
        datasource.sheet_id = meta["sheet_id"]
        datasource.sheet_tab = meta["resolved_tab"]
        datasource = sheet_datasource_repo.mark_ready(
            db,
            datasource,
            row_count=meta["row_count"],
            column_count=meta["column_count"],
            column_names_json=meta["column_names_json"],
            sheet_tabs_json=meta["sheet_tabs_json"],
        )
    except HTTPException as exc:
        sheet_datasource_repo.mark_failed(db, datasource, error_message=exc.detail)
        raise
    except Exception as exc:
        sheet_datasource_repo.mark_failed(db, datasource, error_message=str(exc))
        raise HTTPException(
            status_code=400, detail=f"Failed to connect to Google Sheet: {exc}"
        ) from exc

    return datasource


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

def query_datasource(
    db: Session,
    *,
    datasource_id: uuid.UUID,
    user: User,
    question: str,
    sheet_tab: Optional[str] = None,
) -> dict:
    """
    Answer a natural-language question about the data in the given datasource.
    Returns dict with: answer, table, execution_duration_ms, datasource_id.
    """
    datasource = sheet_datasource_repo.get(db, datasource_id, user.id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found.")

    if datasource.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Datasource is not ready (status: {datasource.status}). Please wait or re-upload.",
        )

    # Resolve sheet tab
    resolved_tab = sheet_tab or datasource.sheet_tab

    # Load the DataFrame
    if datasource.source_type in ("csv", "xlsx"):
        if not datasource.storage_path:
            raise HTTPException(status_code=400, detail="No storage path for this datasource.")
        df = load_dataframe(datasource.storage_path, sheet_tab=resolved_tab)
    elif datasource.source_type == "google_sheets":
        if not datasource.sheet_url:
            raise HTTPException(status_code=400, detail="No sheet URL for this datasource.")
        df = load_google_sheet(datasource.sheet_url, sheet_tab=resolved_tab)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unknown source type: {datasource.source_type}"
        )

    result = run_sheet_query(df, question=question)
    result["datasource_id"] = datasource.id
    result["chat_id"] = datasource.chat_id
    return result


# ---------------------------------------------------------------------------
# List / delete
# ---------------------------------------------------------------------------

def list_chat_datasources(
    db: Session, *, chat_id: uuid.UUID, user: User
) -> list[SheetDatasource]:
    return sheet_datasource_repo.list_for_chat(db, chat_id=chat_id, user_id=user.id)


def delete_datasource(db: Session, *, datasource_id: uuid.UUID, user: User) -> None:
    datasource = sheet_datasource_repo.get(db, datasource_id, user.id)
    if not datasource:
        raise HTTPException(status_code=404, detail="Datasource not found.")

    # Remove file from disk if applicable
    if datasource.storage_path:
        try:
            Path(datasource.storage_path).unlink(missing_ok=True)
        except Exception:
            pass  # Best-effort

    sheet_datasource_repo.delete(db, datasource)
