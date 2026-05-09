from app.ai.chains.chat_chain import generate_reply
from app.ai.llm import resolve_model_name
from app.models.user import User
from app.repositories.chat_repo import get_chat_for_user
from app.repositories.message_repo import create_message
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_thread_service import create_chat
from sqlalchemy.orm import Session


def create_chat_response(request: ChatRequest, db: Session, current_user: User) -> ChatResponse:
    chat = None
    if request.chat_id:
        chat = get_chat_for_user(db, request.chat_id, current_user.id)
    if chat is None:
        chat = create_chat(db, current_user.id)

    create_message(db, chat.id, "user", request.message)
    reply = generate_reply(request)
    create_message(db, chat.id, "assistant", reply)
    return ChatResponse(reply=reply, model=resolve_model_name(), chat_id=chat.id)
