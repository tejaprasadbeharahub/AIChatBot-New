import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.chat_repo import get_chat_for_user
from app.schemas.pdf_rag import (
    PdfChunkMatch,
    PdfDocumentRead,
    PdfQueryRequest,
    PdfQueryResponse,
    PdfUploadResponse,
)
from app.services import attachment_service, pdf_rag_service


router = APIRouter(prefix="/pdf-rag", tags=["pdf-rag"])


def _process_document_in_background(document_id: uuid.UUID) -> None:
    # New session for background task processing.
    from app.db.session import _make_session_factory

    session = _make_session_factory()()
    try:
        pdf_rag_service.process_pdf_document(session, document_id=document_id)
    finally:
        session.close()


@router.post("/upload", response_model=PdfUploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    chat_id: str = Form(...),
    message_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PdfUploadResponse:
    try:
        chat_uuid = uuid.UUID(chat_id)
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID in chat_id or message_id")

    chat = get_chat_for_user(db, chat_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    pdf_rag_service.validate_pdf_upload(file)
    pdf_rag_service.assert_message_belongs_to_chat(db, message_id=message_uuid, chat_id=chat_uuid)

    attachment_data = await attachment_service.process_and_store_attachment(
        file=file,
        message_id=message_uuid,
        file_type="document",
        db=db,
    )

    attachment_id = attachment_data["id"]
    pdf_rag_service.assert_pdf_not_already_indexed_for_attachment(db, attachment_id)

    document = pdf_rag_service.create_pdf_document_from_attachment(
        db,
        attachment_id=attachment_id,
        message_id=message_uuid,
        chat_id=chat_uuid,
        user_id=current_user.id,
        file_name=attachment_data["file_name"],
        storage_path=attachment_data["storage_path"],
    )

    background_tasks.add_task(_process_document_in_background, document.id)
    return PdfUploadResponse(document=PdfDocumentRead.model_validate(document))


@router.post("/process/{document_id}", response_model=PdfDocumentRead)
def process_pdf_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PdfDocumentRead:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id format")

    existing = pdf_rag_service.get_pdf_document(db, doc_uuid, current_user.id)
    processed = pdf_rag_service.process_pdf_document(db, document_id=existing.id)
    return PdfDocumentRead.model_validate(processed)


@router.get("/documents/{document_id}", response_model=PdfDocumentRead)
def get_document_status(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PdfDocumentRead:
    try:
        doc_uuid = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document_id format")

    document = pdf_rag_service.get_pdf_document(db, doc_uuid, current_user.id)
    return PdfDocumentRead.model_validate(document)


@router.get("/chat/{chat_id}/documents", response_model=list[PdfDocumentRead])
def get_chat_documents(
    chat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PdfDocumentRead]:
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    chat = get_chat_for_user(db, chat_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    docs = pdf_rag_service.list_chat_documents(db, chat_uuid, current_user.id)
    return [PdfDocumentRead.model_validate(item) for item in docs]


@router.post("/chat/{chat_id}/query", response_model=PdfQueryResponse)
def query_chat_documents(
    chat_id: str,
    payload: PdfQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PdfQueryResponse:
    try:
        chat_uuid = uuid.UUID(chat_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chat_id format")

    chat = get_chat_for_user(db, chat_uuid, current_user.id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    matches = pdf_rag_service.retrieve_chat_context(
        db,
        user_id=current_user.id,
        chat_id=chat_uuid,
        query=payload.query,
        top_k=payload.top_k,
    )

    return PdfQueryResponse(
        query=payload.query,
        chat_id=chat_uuid,
        matches=[
            PdfChunkMatch(
                chunk_id=item.chunk_id,
                content=item.content,
                document_id=item.document_id,
                file_name=item.file_name,
                chunk_index=item.chunk_index,
                score=item.score,
            )
            for item in matches
        ],
    )
