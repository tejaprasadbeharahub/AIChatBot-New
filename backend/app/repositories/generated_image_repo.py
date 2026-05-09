import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.generated_image import GeneratedImage


def create_generated_image(
    db: Session,
    prompt: str,
    message_id: uuid.UUID,
    chat_id: uuid.UUID,
) -> GeneratedImage:
    """Create a new generated image record with pending status"""
    image = GeneratedImage(
        prompt=prompt,
        message_id=message_id,
        chat_id=chat_id,
        status="pending",
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def get_generated_image(db: Session, image_id: uuid.UUID) -> GeneratedImage | None:
    """Retrieve a generated image by ID"""
    return db.query(GeneratedImage).filter(GeneratedImage.id == image_id).first()


def get_images_for_message(db: Session, message_id: uuid.UUID) -> list[GeneratedImage]:
    """Retrieve all generated images for a specific message"""
    return db.query(GeneratedImage).filter(GeneratedImage.message_id == message_id).all()


def get_images_for_chat(db: Session, chat_id: uuid.UUID, limit: int = 50) -> list[GeneratedImage]:
    """Retrieve generated images for a chat thread"""
    return (
        db.query(GeneratedImage)
        .filter(GeneratedImage.chat_id == chat_id)
        .order_by(GeneratedImage.generation_timestamp.desc())
        .limit(limit)
        .all()
    )


def update_image_completion(
    db: Session,
    image_id: uuid.UUID,
    status: str,
    image_url: str | None = None,
    image_path: str | None = None,
    error_message: str | None = None,
) -> GeneratedImage | None:
    """Update image generation status after completion or failure"""
    from datetime import datetime, timezone

    image = get_generated_image(db, image_id)
    if not image:
        return None

    image.status = status
    image.image_url = image_url
    image.image_path = image_path
    image.error_message = error_message
    image.completion_timestamp = datetime.now(timezone.utc)

    db.commit()
    db.refresh(image)
    return image


def delete_generated_image(db: Session, image_id: uuid.UUID) -> bool:
    """Delete a generated image record"""
    image = get_generated_image(db, image_id)
    if not image:
        return False

    db.delete(image)
    db.commit()
    return True
