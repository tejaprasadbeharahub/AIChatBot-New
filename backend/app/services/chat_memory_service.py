import uuid

from sqlalchemy.orm import Session

from app.repositories.message_repo import get_recent_messages_for_chat
from app.schemas.chat import ChatMessage


def get_thread_memory(db: Session, chat_id: uuid.UUID, max_turns: int) -> list[ChatMessage]:
    """Return chronological short-term memory for a single chat thread.

    A turn is treated as one user-assistant exchange, so we load up to 2 * max_turns
    persisted messages and keep them in chronological order.
    """
    message_limit = max(max_turns, 0) * 2
    if message_limit == 0:
        return []

    messages = get_recent_messages_for_chat(db, chat_id=chat_id, limit=message_limit)
    return [ChatMessage(role=message.role, content=message.content) for message in messages]
