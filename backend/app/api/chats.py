import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.chat_repo import get_chat_by_id
from app.repositories.message_repo import get_messages_for_chat
from app.schemas.chat import ChatRead, ChatUpdateRequest
from app.schemas.message import MessageRead
from app.services.chat_thread_service import create_chat as create_chat_thread
from app.services.chat_thread_service import delete_chat, get_user_chats, update_chat_title

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatRead])
def list_chats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ChatRead]:
    """Return all chats belonging to the authenticated user."""
    return get_user_chats(db, user_id=current_user.id)  # type: ignore[return-value]


@router.post("", response_model=ChatRead, status_code=status.HTTP_201_CREATED)
def create_chat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatRead:
    return create_chat_thread(db, user_id=current_user.id)  # type: ignore[return-value]


@router.put("/{chat_id}", response_model=ChatRead)
def rename_chat(
    chat_id: uuid.UUID,
    payload: ChatUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ChatRead:
    chat = update_chat_title(db, chat_id=chat_id, user_id=current_user.id, new_title=payload.title)
    if chat is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return chat  # type: ignore[return-value]


@router.delete("/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_chat(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    deleted = delete_chat(db, chat_id=chat_id, user_id=current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")


@router.get("/{chat_id}/messages", response_model=list[MessageRead])
def list_messages(
    chat_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[MessageRead]:
    """Return all messages for a specific chat (must belong to the current user)."""
    chat = get_chat_by_id(db, chat_id=chat_id)
    if chat is None or chat.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    return get_messages_for_chat(db, chat_id=chat_id)  # type: ignore[return-value]
