import uuid

from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.models.message import Message
from app.repositories.chat_repo import touch_chat


def get_messages_for_chat(db: Session, chat_id: uuid.UUID) -> list[Message]:
    return (
        db.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.timestamp.asc())
        .all()
    )


def create_message(db: Session, chat_id: uuid.UUID, role: str, content: str) -> Message:
    message = Message(chat_id=chat_id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if chat is not None:
        touch_chat(db, chat)
    return message
