from datetime import datetime, timezone
import uuid

from sqlalchemy.orm import Session

from app.models.chat import Chat
from app.repositories.chat_repo import (
    create_chat as create_chat_row,
    delete_chat as delete_chat_row,
    get_chat_for_user,
    get_chats_for_user as get_user_chat_rows,
    update_chat_title as update_chat_title_row,
)


def generate_chat_title(user_id: uuid.UUID, timestamp: datetime) -> str:
    # user_id is part of the function contract for future personalization rules.
    _ = user_id
    return f"New Chat - {timestamp.strftime('%b %d')}"


def create_chat(db: Session, user_id: uuid.UUID) -> Chat:
    now = datetime.now(timezone.utc)
    title = generate_chat_title(user_id=user_id, timestamp=now)
    return create_chat_row(db, user_id=user_id, title=title)


def get_user_chats(db: Session, user_id: uuid.UUID) -> list[Chat]:
    return get_user_chat_rows(db, user_id)


def update_chat_title(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID, new_title: str) -> Chat | None:
    chat = get_chat_for_user(db, chat_id=chat_id, user_id=user_id)
    if chat is None:
        return None
    return update_chat_title_row(db, chat=chat, new_title=new_title)


def delete_chat(db: Session, chat_id: uuid.UUID, user_id: uuid.UUID) -> bool:
    chat = get_chat_for_user(db, chat_id=chat_id, user_id=user_id)
    if chat is None:
        return False
    delete_chat_row(db, chat)
    return True
