from app.ai.chains.chat_chain import generate_reply
from app.ai.llm import resolve_model_name
from app.core.config import settings
from app.models.user import User
from app.repositories.chat_repo import get_chat_for_user
from app.repositories.message_repo import create_message
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_memory_service import get_thread_memory
from app.services.chat_thread_service import create_chat
from app.services import pdf_rag_service
from sqlalchemy.orm import Session


def _build_model_input(message: str, attachment_context: list[str]) -> str:
    if not attachment_context:
        return message

    lines = [message, "", "[Attachment metadata provided by user]"]
    lines.extend(f"- {item}" for item in attachment_context)
    return "\n".join(lines)


def create_chat_response(request: ChatRequest, db: Session, current_user: User) -> ChatResponse:
    chat = None
    if request.chat_id:
        chat = get_chat_for_user(db, request.chat_id, current_user.id)
    if chat is None:
        chat = create_chat(db, current_user.id)

    normalized_user_message = request.message.strip()
    if not normalized_user_message:
        normalized_user_message = "Please help me with this request."

    memory = get_thread_memory(db, chat_id=chat.id, max_turns=settings.chat_memory_turns)
    user_message = create_message(db, chat.id, "user", normalized_user_message)
    model_input = _build_model_input(normalized_user_message, request.attachment_context)

    try:
        rag_matches = pdf_rag_service.retrieve_chat_context(
            db,
            user_id=current_user.id,
            chat_id=chat.id,
            query=normalized_user_message,
            top_k=settings.rag_top_k,
        )
        rag_context = pdf_rag_service.build_rag_context_block(rag_matches)
        if rag_context:
            model_input = f"{model_input}\n\n{rag_context}"
    except Exception:
        # Gracefully continue even when retrieval fails.
        pass

    reply = (generate_reply(message=model_input, history=memory, temperature=request.temperature) or "").strip()
    if not reply:
        reply = "I could not generate a response. Please try again."
    create_message(db, chat.id, "assistant", reply)
    return ChatResponse(reply=reply, model=resolve_model_name(), chat_id=chat.id, user_message_id=user_message.id)
