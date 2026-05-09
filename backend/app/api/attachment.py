import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.repositories import attachment_repo
from app.schemas.attachment import AttachmentMetadata, AttachmentTextExtraction
from app.services import attachment_service


router = APIRouter(prefix="/attachments", tags=["attachments"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_attachment(
    message_id: str = Form(...),
    file_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttachmentMetadata:
    """
    Upload an attachment to a specific message.
    
    - **message_id**: UUID of the message to attach to
    - **file_type**: Type of attachment (image, video, code, formula, document)
    - **file**: The file to upload
    """
    try:
        message_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")

    # Validate file type
    if file_type not in attachment_service.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file_type. Allowed: {list(attachment_service.ALLOWED_FILE_TYPES.keys())}",
        )

    try:
        attachment_data = await attachment_service.process_and_store_attachment(
            file=file,
            message_id=message_uuid,
            file_type=file_type,
            db=db,
        )
        return AttachmentMetadata(**attachment_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Attachment upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/download/{attachment_id}")
async def download_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """
    Download an attachment by ID.
    """
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid attachment_id format")

    attachment = attachment_repo.get_attachment(db, att_uuid)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Verify file exists
    file_path = attachment_service.get_file_path(attachment.storage_path)
    if not file_path.exists():
        logger.error(f"Attachment file not found: {file_path}")
        raise HTTPException(status_code=404, detail="Attachment file not found")

    return FileResponse(
        path=file_path,
        filename=attachment.file_name,
        media_type=attachment.mime_type,
    )


@router.delete("/{attachment_id}")
async def delete_attachment(
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Delete an attachment by ID.
    """
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid attachment_id format")

    success = await attachment_service.delete_attachment_with_file(db, att_uuid)
    if not success:
        raise HTTPException(status_code=404, detail="Attachment not found")

    return {"message": "Attachment deleted successfully"}


@router.get("/message/{message_id}")
async def get_message_attachments(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AttachmentMetadata]:
    """
    Get all attachments for a specific message.
    """
    try:
        msg_uuid = uuid.UUID(message_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid message_id format")

    attachments = attachment_repo.get_attachments_for_message(db, msg_uuid)
    return [AttachmentMetadata.model_validate(att) for att in attachments]


@router.post("/extract-text/{attachment_id}")
async def extract_attachment_text(
    attachment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AttachmentTextExtraction:
    """Extract visible text from an uploaded image attachment."""
    try:
        att_uuid = uuid.UUID(attachment_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid attachment_id format")

    extracted_text = attachment_service.extract_text_from_image_attachment(db, att_uuid)
    attachment = attachment_repo.get_attachment(db, att_uuid)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    summary_text = attachment_service.summarize_attachment_content(
        extracted_text=extracted_text,
        attachment_type=attachment.file_type,
        file_name=attachment.file_name,
    )
    return AttachmentTextExtraction(
        attachment_id=att_uuid,
        attachment_type=attachment.file_type,
        extracted_text=extracted_text,
        summary_text=summary_text,
    )
