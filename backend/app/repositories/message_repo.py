import uuid

from sqlalchemy.orm import Session, selectinload

from app.models.chat import Chat
from app.models.message import Message
from app.repositories.chat_repo import touch_chat


def get_messages_for_chat(db: Session, chat_id: uuid.UUID) -> list[Message]:
    return (
        db.query(Message)
        .options(selectinload(Message.attachments))
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp.asc())
        .all()
    )


def get_recent_messages_for_chat(db: Session, chat_id: uuid.UUID, limit: int) -> list[Message]:
    if limit <= 0:
        return []

    recent = (
        db.query(Message)
        .options(selectinload(Message.attachments))
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp.desc(), Message.id.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(recent))


def create_message(db: Session, chat_id: uuid.UUID, role: str, content: str) -> Message:
    normalized_content = (content or "").strip()

    # Keep persisted chat history valid for pydantic models that require min_length=1.
    if role == "user" and not normalized_content:
        raise ValueError("Message content cannot be empty")
    if role == "assistant" and not normalized_content:
        normalized_content = "I could not generate a response. Please try again."

    message = Message(chat_id=chat_id, role=role, content=normalized_content)
    db.add(message)
    db.commit()
    db.refresh(message)
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat is not None:
        touch_chat(db, chat)
    return message
