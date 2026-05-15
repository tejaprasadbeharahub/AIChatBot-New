"""
FastAPI router for Research Digest Agent.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.chat_repo import get_chat_for_user
from app.repositories.message_repo import create_message
from app.schemas.research_agent import ResearchQueryRequest, ResearchDigestResponse
from app.services.research_agent.agent import ResearchAgent, validate_research_agent_dependencies

router = APIRouter(prefix="/research-agent", tags=["research-agent"])
logger = logging.getLogger(__name__)


@router.on_event("startup")
async def validate_dependencies():
    """Validate research agent dependencies on startup."""
    try:
        validate_research_agent_dependencies()
    except RuntimeError as exc:
        logger.warning(f"Research agent dependencies missing: {exc}")


@router.post("/research-stream")
async def research_stream(
    request: ResearchQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start research and stream updates in real-time using Server-Sent Events (SSE).

    Returns: Stream of events as they happen
    """
    async def event_generator():
        session = None
        research_task: asyncio.Task | None = None
        try:
            # Get or create chat
            chat_id = request.chat_id or uuid.uuid4()
            chat = get_chat_for_user(db, chat_id, current_user.id)
            if not chat and not request.chat_id:
                # Create new chat for research
                from app.repositories.chat_repo import create_chat
                chat = create_chat(db, user_id=current_user.id, title=f"Research: {request.query[:50]}")
                chat_id = chat.id

            # Create research session
            from app.models.research_session import ResearchSession
            session = ResearchSession(
                chat_id=chat_id,
                user_id=current_user.id,
                research_query=request.query,
                status="in_progress",
            )
            db.add(session)
            db.commit()

            # Create user message
            user_message = create_message(
                db,
                chat_id,
                "user",
                f"Research: {request.query}",
            )

            # Stream starting event
            yield f"data: {json.dumps({'event': 'started', 'session_id': str(session.id)})}\n\n"

            # Initialize agent
            agent = ResearchAgent(db, current_user.id, chat_id)

            event_queue: asyncio.Queue[dict[str, object]] = asyncio.Queue()

            # Define event callback (async and awaitable)
            async def on_event(event: dict):
                await event_queue.put({
                    "event": event["event_type"],
                    "data": event["data"],
                    "timestamp": event["timestamp"],
                })

            async def run_research_job() -> dict:
                return await agent.research(
                    query=request.query,
                    max_papers=request.max_papers,
                    depth=request.depth,
                    on_event=on_event,
                )

            research_task = asyncio.create_task(run_research_job())

            # Stream incremental events while background job runs.
            while True:
                if research_task.done() and event_queue.empty():
                    break

                try:
                    queued_event = await asyncio.wait_for(event_queue.get(), timeout=0.25)
                    yield f"data: {json.dumps(queued_event)}\n\n"
                except asyncio.TimeoutError:
                    continue

            result = await research_task

            # Create assistant message with digest
            digest_json = result["digest"].model_dump_json()
            assistant_content = (
                f"Research completed on: {request.query}\n\n"
                f"Papers found: {result['papers']}\n\n"
                f"[RESEARCH_DIGEST]{digest_json}"
            )

            assistant_message = create_message(
                db,
                chat_id,
                "assistant",
                assistant_content,
            )

            # Update session
            session.status = "completed"
            session.papers_found = len(result["papers"])
            session.digest_full = digest_json
            session.message_id = assistant_message.id
            session.completed_at = datetime.now(timezone.utc)
            db.commit()

            # Stream final response
            yield f"data: {json.dumps({
                'event': 'completed',
                'session_id': str(session.id),
                'assistant_message_id': str(assistant_message.id),
                'user_message_id': str(user_message.id),
                'papers_found': len(result['papers']),
                'duration_seconds': result['duration_seconds'],
                'data': {
                    'digest': result['digest'].model_dump(),
                },
            })}\n\n"

        except Exception as exc:
            logger.exception("Research stream error")
            yield f"data: {json.dumps({'event': 'error', 'message': str(exc)})}\n\n"
            if session is not None:
                session.status = "failed"
                session.error_message = str(exc)
                db.commit()
        finally:
            if research_task and not research_task.done():
                research_task.cancel()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/research")
async def research(
    request: ResearchQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResearchDigestResponse:
    """
    Start research and wait for completion (non-streaming).

    For better UX, use /research-stream endpoint instead.
    """
    try:
        # Get or create chat
        chat_id = request.chat_id or uuid.uuid4()
        chat = get_chat_for_user(db, chat_id, current_user.id)
        if not chat and not request.chat_id:
            from app.repositories.chat_repo import create_chat
            chat = create_chat(db, user_id=current_user.id, title=f"Research: {request.query[:50]}")
            chat_id = chat.id

        # Create research session
        from app.models.research_session import ResearchSession
        session = ResearchSession(
            chat_id=chat_id,
            user_id=current_user.id,
            research_query=request.query,
            status="in_progress",
        )
        db.add(session)
        db.commit()

        # Create user message
        user_message = create_message(db, chat_id, "user", f"Research: {request.query}")

        # Run research
        agent = ResearchAgent(db, current_user.id, chat_id)
        result = await agent.research(
            query=request.query,
            max_papers=request.max_papers,
            depth=request.depth,
        )

        # Create assistant message
        digest_json = result["digest"].model_dump_json()
        assistant_content = (
            f"Research completed on: {request.query}\n\n"
            f"[RESEARCH_DIGEST]{digest_json}"
        )
        assistant_message = create_message(db, chat_id, "assistant", assistant_content)

        # Update session
        session.status = "completed"
        session.papers_found = len(result["papers"])
        session.digest_full = digest_json
        session.message_id = assistant_message.id
        session.completed_at = datetime.now(timezone.utc)
        db.commit()

        return ResearchDigestResponse(
            session_id=session.id,
            chat_id=chat_id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            query=request.query,
            digest=result["digest"],
            search_duration_seconds=result["duration_seconds"],
            papers_found=len(result["papers"]),
        )

    except Exception as exc:
        logger.exception("Research failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
