import re
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

import chromadb
from fastapi import HTTPException, UploadFile
from openai import OpenAI
from pypdf import PdfReader
from sqlalchemy.orm import Session

from app.ai.llm import DEFAULT_LITELLM_PROXY_URL
from app.core.config import settings
from app.models.message import Message
from app.models.pdf_document import PdfDocument
from app.repositories import attachment_repo, pdf_document_repo
from app.services import attachment_service


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    document_id: uuid.UUID
    file_name: str
    chunk_index: int
    score: float


def _normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _get_embedding_model() -> str:
    return (settings.litellm_embedding_model or "text-embedding-3-large").strip()


def _get_embedding_client() -> OpenAI:
    api_key = settings.litellm_api_key
    if not api_key:
        raise HTTPException(status_code=500, detail="Missing LITELLM_API_KEY in backend configuration")

    proxy_url = (settings.litellm_proxy_url or DEFAULT_LITELLM_PROXY_URL).rstrip("/")
    base_url = proxy_url if proxy_url.endswith("/v1") else f"{proxy_url}/v1"
    return OpenAI(api_key=api_key, base_url=base_url)


def _get_chroma_client() -> Any:
    chroma_api_key = (settings.chroma_api_key or "").strip()
    chroma_host = (settings.chroma_host or "").strip()
    chroma_tenant = (settings.chroma_tenant_id or "").strip()
    chroma_database = (settings.chroma_database or "").strip()

    # Use Chroma Cloud when all cloud settings are present.
    if chroma_api_key and chroma_host and chroma_tenant and chroma_database:
        parsed = urlparse(chroma_host if "://" in chroma_host else f"https://{chroma_host}")
        host = parsed.hostname or chroma_host
        ssl = (parsed.scheme or "https").lower() == "https"
        port = parsed.port or (443 if ssl else 80)

        headers = {
            "x-chroma-token": chroma_api_key,
            "Authorization": f"Bearer {chroma_api_key}",
        }
        return chromadb.HttpClient(
            host=host,
            port=port,
            ssl=ssl,
            headers=headers,
            tenant=chroma_tenant,
            database=chroma_database,
        )

    persist_dir = settings.chroma_persist_dir or "./chroma_db"
    return chromadb.PersistentClient(path=persist_dir)


def _build_collection_name(user_id: uuid.UUID, chat_id: uuid.UUID) -> str:
    return f"pdfrag_u_{user_id.hex[:16]}_c_{chat_id.hex[:16]}"


def _extract_pdf_text(file_path) -> str:
    try:
        pdf = PdfReader(str(file_path))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid or corrupted PDF file") from exc

    blocks: list[str] = []
    for page in pdf.pages:
        text = _normalize_text(page.extract_text() or "")
        if text:
            blocks.append(text)

    combined = "\n\n".join(blocks).strip()
    if not combined:
        raise HTTPException(status_code=400, detail="No extractable text found in PDF")
    return combined


def _chunk_text(text: str) -> list[str]:
    chunk_size = max(200, settings.rag_chunk_size)
    overlap = max(0, min(settings.rag_chunk_overlap, chunk_size // 2))

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_len:
            break
        start = max(end - overlap, start + 1)

    return chunks


def _embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    client = _get_embedding_client()
    model = _get_embedding_model()
    vectors: list[list[float]] = []
    batch_size = max(1, settings.rag_embedding_batch_size)

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        try:
            response = client.embeddings.create(model=model, input=batch)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Embedding generation failed: {exc}") from exc
        vectors.extend([item.embedding for item in response.data])

    return vectors


def _embed_query(text: str) -> list[float]:
    client = _get_embedding_client()
    model = _get_embedding_model()
    try:
        response = client.embeddings.create(model=model, input=text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query embedding generation failed: {exc}") from exc
    return response.data[0].embedding


def _to_distance_score(distance: float) -> float:
    return 1.0 / (1.0 + max(0.0, distance))


def validate_pdf_upload(file: UploadFile) -> None:
    file_name = (file.filename or "").strip()
    if not file_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content_type = (file.content_type or "").lower()
    if content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="Unsupported MIME type for PDF upload")


def create_pdf_document_from_attachment(
    db: Session,
    *,
    attachment_id: uuid.UUID,
    message_id: uuid.UUID,
    chat_id: uuid.UUID,
    user_id: uuid.UUID,
    file_name: str,
    storage_path: str,
) -> PdfDocument:
    return pdf_document_repo.create_pdf_document(
        db,
        attachment_id=attachment_id,
        message_id=message_id,
        chat_id=chat_id,
        user_id=user_id,
        file_name=file_name,
        storage_path=storage_path,
        status="pending",
    )


def process_pdf_document(db: Session, *, document_id: uuid.UUID) -> PdfDocument:
    document = pdf_document_repo.get_pdf_document(db, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="PDF document not found")

    pdf_document_repo.mark_processing(db, document)

    try:
        file_path = attachment_service.get_file_path(document.storage_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Uploaded PDF file not found")

        text = _extract_pdf_text(file_path)
        chunks = _chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=400, detail="PDF content is empty after chunking")

        if len(chunks) > settings.rag_max_chunks_per_document:
            raise HTTPException(
                status_code=413,
                detail=f"PDF produced too many chunks ({len(chunks)}). Reduce document size or increase chunk size.",
            )

        vectors = _embed_texts(chunks)
        if len(vectors) != len(chunks):
            raise HTTPException(status_code=500, detail="Embedding vector count mismatch")

        collection_name = _build_collection_name(document.user_id, document.chat_id)
        chroma_client = _get_chroma_client()
        collection = chroma_client.get_or_create_collection(name=collection_name)

        ids = [f"{document.id}:{idx}" for idx in range(len(chunks))]
        metadatas: list[dict[str, Any]] = [
            {
                "document_id": str(document.id),
                "chat_id": str(document.chat_id),
                "user_id": str(document.user_id),
                "file_name": document.file_name,
                "chunk_index": idx,
                "message_id": str(document.message_id),
            }
            for idx in range(len(chunks))
        ]

        try:
            collection.upsert(ids=ids, documents=chunks, embeddings=vectors, metadatas=metadatas)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Vector DB upsert failed: {exc}") from exc

        embedding_model = _get_embedding_model()
        return pdf_document_repo.mark_completed(
            db,
            document,
            chunk_count=len(chunks),
            embedding_model=embedding_model,
            vector_collection_id=collection_name,
        )
    except HTTPException as exc:
        pdf_document_repo.mark_failed(db, document, str(exc.detail))
        raise
    except Exception as exc:
        pdf_document_repo.mark_failed(db, document, str(exc))
        raise HTTPException(status_code=500, detail=f"PDF processing failed: {exc}") from exc


def get_pdf_document(db: Session, document_id: uuid.UUID, user_id: uuid.UUID) -> PdfDocument:
    document = pdf_document_repo.get_pdf_document(db, document_id)
    if not document or document.user_id != user_id:
        raise HTTPException(status_code=404, detail="PDF document not found")
    return document


def list_chat_documents(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID) -> list[PdfDocument]:
    return pdf_document_repo.list_chat_pdf_documents(db, chat_id=chat_id, user_id=user_id)


def retrieve_chat_context(
    db: Session,
    *,
    user_id: uuid.UUID,
    chat_id: uuid.UUID,
    query: str,
    top_k: int | None = None,
) -> list[RetrievedChunk]:
    del db
    if not query.strip():
        return []

    k = top_k if top_k is not None else settings.rag_top_k
    if k <= 0:
        return []

    collection_name = _build_collection_name(user_id, chat_id)
    chroma_client = _get_chroma_client()

    try:
        collection = chroma_client.get_collection(name=collection_name)
    except Exception:
        return []

    embedding = _embed_query(query)

    try:
        result = collection.query(query_embeddings=[embedding], n_results=k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector retrieval failed: {exc}") from exc

    ids = (result.get("ids") or [[]])[0]
    docs = (result.get("documents") or [[]])[0]
    metas = (result.get("metadatas") or [[]])[0]
    distances = (result.get("distances") or [[]])[0]

    matches: list[RetrievedChunk] = []
    for idx, chunk_id in enumerate(ids):
        metadata = metas[idx] if idx < len(metas) else {}
        content = docs[idx] if idx < len(docs) else ""
        distance = float(distances[idx]) if idx < len(distances) and distances[idx] is not None else 0.0

        try:
            document_id = uuid.UUID(str(metadata.get("document_id", "")))
        except Exception:
            continue

        matches.append(
            RetrievedChunk(
                chunk_id=chunk_id,
                content=content,
                document_id=document_id,
                file_name=str(metadata.get("file_name", "unknown.pdf")),
                chunk_index=int(metadata.get("chunk_index", 0)),
                score=_to_distance_score(distance),
            )
        )

    return matches


def build_rag_context_block(matches: list[RetrievedChunk]) -> str:
    if not matches:
        return ""

    lines = ["[Retrieved PDF context]"]
    for item in matches:
        lines.append(
            f"- source={item.file_name} chunk={item.chunk_index} relevance={item.score:.3f}: {item.content}"
        )
    return "\n".join(lines)


def assert_message_belongs_to_chat(db: Session, *, message_id: uuid.UUID, chat_id: uuid.UUID) -> Message:
    message = db.query(Message).filter(Message.id == message_id, Message.chat_id == chat_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found in chat")
    return message


def assert_pdf_not_already_indexed_for_attachment(db: Session, attachment_id: uuid.UUID) -> None:
    all_docs = db.query(PdfDocument).filter(PdfDocument.attachment_id == attachment_id).count()
    if all_docs > 0:
        raise HTTPException(status_code=409, detail="This PDF attachment is already indexed")


def get_attachment_for_document_upload(db: Session, attachment_id: uuid.UUID):
    attachment = attachment_repo.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment
