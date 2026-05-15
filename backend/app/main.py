from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.attachment import router as attachment_router
from app.api.chat import router as chat_router
from app.api.chats import router as chats_router
from app.api.image_generation import router as image_generation_router
from app.api.nl_sql import router as nl_sql_router
from app.api.pdf_rag import router as pdf_rag_router
from app.api.sheet_agent import router as sheet_agent_router
from app.core.config import settings
from app.services.sheet_agent.agent import validate_sheet_agent_dependencies


app = FastAPI(title=settings.app_name or "amzur-ai-chat")

# CORS must be registered before routes so preflight and actual requests are handled consistently.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allowed_methods_list(),
    allow_headers=settings.cors_allowed_headers_list(),
)

app.include_router(chat_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(chats_router, prefix="/api")
app.include_router(attachment_router, prefix="/api")
app.include_router(image_generation_router, prefix="/api")
app.include_router(nl_sql_router, prefix="/api")
app.include_router(pdf_rag_router, prefix="/api")
app.include_router(sheet_agent_router, prefix="/api")


@app.on_event("startup")
async def validate_optional_runtime_dependencies() -> None:
    validate_sheet_agent_dependencies()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
