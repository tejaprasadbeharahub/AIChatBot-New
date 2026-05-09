import uuid

from sqlalchemy.orm import Session

from app.models.attachment import Attachment


def create_attachment(
    db: Session,
    message_id: uuid.UUID,
    file_name: str,
    file_type: str,
    mime_type: str,
    file_size: int,
    storage_path: str,
) -> Attachment:
    """Create a new attachment record"""
    attachment = Attachment(
        message_id=message_id,
        file_name=file_name,
        file_type=file_type,
        mime_type=mime_type,
        file_size=file_size,
        storage_path=storage_path,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def get_attachment(db: Session, attachment_id: uuid.UUID) -> Attachment | None:
    """Get attachment by ID"""
    return db.query(Attachment).filter(Attachment.id == attachment_id).first()


def get_attachments_for_message(db: Session, message_id: uuid.UUID) -> list[Attachment]:
    """Get all attachments for a specific message"""
    return (
        db.query(Attachment)
        .filter(Attachment.message_id == message_id)
        .order_by(Attachment.upload_timestamp.asc())
        .all()
    )


def get_attachments_for_chat(db: Session, chat_id: uuid.UUID) -> list[Attachment]:
    """Get all attachments for a chat (through messages)"""
    from app.models.message import Message

    return (
        db.query(Attachment)
        .join(Message, Attachment.message_id == Message.id)
        .filter(Message.chat_id == chat_id)
        .order_by(Attachment.upload_timestamp.asc())
        .all()
    )


def delete_attachment(db: Session, attachment_id: uuid.UUID) -> bool:
    """Delete attachment by ID"""
    attachment = get_attachment(db, attachment_id)
    if attachment:
        db.delete(attachment)
        db.commit()
        return True
    return False


def delete_attachments_for_message(db: Session, message_id: uuid.UUID) -> int:
    """Delete all attachments for a message"""
    count = db.query(Attachment).filter(Attachment.message_id == message_id).delete()
    db.commit()
    return count
