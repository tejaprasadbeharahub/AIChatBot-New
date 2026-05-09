import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.pdf_document import PdfDocument


def create_pdf_document(
    db: Session,
    *,
    attachment_id: uuid.UUID,
    message_id: uuid.UUID,
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    file_name: str,
    storage_path: str,
    status: str = "pending",
) -> PdfDocument:
    document = PdfDocument(
        attachment_id=attachment_id,
        message_id=message_id,
        chat_id=chat_id,
        user_id=user_id,
        file_name=file_name,
        storage_path=storage_path,
        status=status,
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_pdf_document(db: Session, document_id: uuid.UUID) -> PdfDocument | None:
    return db.query(PdfDocument).filter(PdfDocument.id == document_id).first()


def list_chat_pdf_documents(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID) -> list[PdfDocument]:
    return (
        db.query(PdfDocument)
        .filter(PdfDocument.chat_id == chat_id, PdfDocument.user_id == user_id)
        .order_by(PdfDocument.upload_timestamp.desc())
        .all()
    )


def list_user_pdf_documents(db: Session, user_id: uuid.UUID, limit: int = 100) -> list[PdfDocument]:
    return (
        db.query(PdfDocument)
        .filter(PdfDocument.user_id == user_id)
        .order_by(PdfDocument.upload_timestamp.desc())
        .limit(limit)
        .all()
    )


def update_pdf_document_status(
    db: Session,
    document: PdfDocument,
    *,
    status: str,
    chunk_count: int | None = None,
    embedding_model: str | None = None,
    vector_collection_id: str | None = None,
    error_message: str | None = None,
    processed_at: datetime | None = None,
) -> PdfDocument:
    document.status = status
    if chunk_count is not None:
        document.chunk_count = chunk_count
    if embedding_model is not None:
        document.embedding_model = embedding_model
    if vector_collection_id is not None:
        document.vector_collection_id = vector_collection_id
    document.error_message = error_message
    document.processed_at = processed_at
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def mark_processing(db: Session, document: PdfDocument) -> PdfDocument:
    return update_pdf_document_status(db, document, status="processing", error_message=None)


def mark_failed(db: Session, document: PdfDocument, error_message: str) -> PdfDocument:
    return update_pdf_document_status(
        db,
        document,
        status="failed",
        error_message=error_message,
        processed_at=datetime.now(timezone.utc),
    )


def mark_completed(
    db: Session,
    document: PdfDocument,
    *,
    chunk_count: int,
    embedding_model: str,
    vector_collection_id: str,
) -> PdfDocument:
    return update_pdf_document_status(
        db,
        document,
        status="completed",
        chunk_count=chunk_count,
        embedding_model=embedding_model,
        vector_collection_id=vector_collection_id,
        error_message=None,
        processed_at=datetime.now(timezone.utc),
    )
