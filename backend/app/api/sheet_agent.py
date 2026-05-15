"""
FastAPI router for the Sheet Agent — CSV / XLSX / Google Sheets NL query feature.
"""

import uuid
import logging
import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.chat_repo import get_chat_for_user
from app.repositories.message_repo import create_message
from app.schemas.sheet_agent import (
    ConnectGoogleSheetRequest,
    ConnectGoogleSheetResponse,
    ListDatasourcesResponse,
    SheetDatasourceRead,
    SheetQueryRequest,
    SheetQueryResponse,
    SheetUploadResponse,
)
from app.services.sheet_agent import service as sheet_service

router = APIRouter(prefix="/sheet-agent", tags=["sheet-agent"])
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Upload CSV / XLSX
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=SheetUploadResponse)
async def upload_sheet(
    chat_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SheetUploadResponse:
    """Upload a CSV or XLSX file and attach it to a chat session."""
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id format.")

    datasource = await sheet_service.upload_sheet_file(
        db, file=file, chat_id=chat_uuid, user=current_user
    )
    return SheetUploadResponse(datasource=SheetDatasourceRead.model_validate(datasource))


# ---------------------------------------------------------------------------
# Connect Google Sheet
# ---------------------------------------------------------------------------

@router.post("/connect-google-sheet", response_model=ConnectGoogleSheetResponse)
def connect_google_sheet(
    payload: ConnectGoogleSheetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConnectGoogleSheetResponse:
    """Connect a Google Sheets spreadsheet to a chat session."""
    datasource = sheet_service.connect_google_sheet(
        db,
        chat_id=payload.chat_id,
        user=current_user,
        sheet_url=payload.sheet_url,
        sheet_tab=payload.sheet_tab,
    )
    return ConnectGoogleSheetResponse(datasource=SheetDatasourceRead.model_validate(datasource))


# ---------------------------------------------------------------------------
# Query datasource
# ---------------------------------------------------------------------------

@router.post("/query", response_model=SheetQueryResponse)
def query_sheet(
    payload: SheetQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SheetQueryResponse:
    """Ask a natural language question about a connected datasource."""
    result = sheet_service.query_datasource(
        db,
        datasource_id=payload.datasource_id,
        user=current_user,
        question=payload.question,
        sheet_tab=payload.sheet_tab,
    )

    resolved_chat_id = payload.chat_id or result["chat_id"]
    chat = get_chat_for_user(db, resolved_chat_id, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found.")

    user_message = create_message(db, chat.id, "user", payload.question)

    # Convert Pydantic model to dict if table exists
    table_data = None
    if result.get("table"):
        table_data = result["table"].model_dump() if hasattr(result["table"], "model_dump") else result["table"].dict()
    
    persisted_sheet_payload = {
        "datasource_id": str(result["datasource_id"]),
        "question": payload.question,
        "answer": result["answer"],
        "table": table_data,
        "execution_duration_ms": result["execution_duration_ms"],
    }
    persisted_assistant_content = (
        f"{result['answer']}\n\n[SHEET_RESULT]{json.dumps(persisted_sheet_payload)}"
    )

    assistant_message = create_message(db, chat.id, "assistant", persisted_assistant_content)

    return SheetQueryResponse(
        chat_id=chat.id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        datasource_id=result["datasource_id"],
        question=payload.question,
        answer=result["answer"],
        table=result.get("table"),
        execution_duration_ms=result["execution_duration_ms"],
    )


# ---------------------------------------------------------------------------
# List datasources for a chat
# ---------------------------------------------------------------------------

@router.get("/chat/{chat_id}/datasources", response_model=ListDatasourcesResponse)
def list_chat_datasources(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ListDatasourcesResponse:
    """List all datasources connected to a chat."""
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id format.")

    items = sheet_service.list_chat_datasources(db, chat_id=chat_uuid, user=current_user)
    return ListDatasourcesResponse(
        items=[SheetDatasourceRead.model_validate(ds) for ds in items]
    )


# ---------------------------------------------------------------------------
# Get single datasource
# ---------------------------------------------------------------------------

@router.get("/datasources/{datasource_id}", response_model=SheetDatasourceRead)
def get_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SheetDatasourceRead:
    """Get metadata for a specific datasource."""
    try:
        ds_uuid = uuid.UUID(datasource_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datasource_id format.")

    from app.repositories import sheet_datasource_repo
    ds = sheet_datasource_repo.get(db, ds_uuid, current_user.id)
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found.")
    return SheetDatasourceRead.model_validate(ds)


# ---------------------------------------------------------------------------
# Delete datasource
# ---------------------------------------------------------------------------

@router.delete("/datasources/{datasource_id}", status_code=204)
def delete_datasource(
    datasource_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a datasource and its associated file."""
    try:
        ds_uuid = uuid.UUID(datasource_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datasource_id format.")

    sheet_service.delete_datasource(db, datasource_id=ds_uuid, user=current_user)
