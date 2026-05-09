from fastapi import APIRouter, HTTPException
import logging
from fastapi import Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import create_chat_response


router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    try:
        return create_chat_response(request, db, current_user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Chat generation failed")
        if settings.environment and settings.environment.lower() == "production":
            raise HTTPException(status_code=500, detail="Chat generation failed") from exc
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {exc}") from exc
