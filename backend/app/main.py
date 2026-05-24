from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all models so SQLAlchemy registers them before mapper configuration
import app.models.chat  # noqa: F401
import app.models.message  # noqa: F401
import app.models.research_session  # noqa: F401

from app.api.auth import router as auth_router
from app.api.agent import router as agent_router
from app.api.analytics import router as analytics_router
from app.api.attachment import router as attachment_router
from app.api.chat import router as chat_router
from app.api.chats import router as chats_router
from app.api.image_generation import router as image_generation_router
from app.api.nl_sql import router as nl_sql_router
from app.api.pdf_rag import router as pdf_rag_router
from app.api.research_agent import router as research_agent_router
from app.api.research import router as research_router
from app.api.sheet_agent import router as sheet_agent_router
from app.api.tictactoe import router as tictactoe_router
from app.api.workflow import router as workflow_router
from app.api.agriculture import router as agriculture_router
from app.core.config import settings
from app.services.sheet_agent.agent import validate_sheet_agent_dependencies
from app.utils.logging import configure_logging

# Import workflow models so SQLAlchemy metadata includes them at startup.
import app.models.workflow_request  # noqa: F401
import app.models.research_result  # noqa: F401
import app.models.daily_report  # noqa: F401
import app.models.crop_diagnosis  # noqa: F401
import app.models.market_intelligence  # noqa: F401
import app.models.risk_prediction  # noqa: F401


app = FastAPI(title=settings.app_name or "amzur-ai-chat")
configure_logging("INFO")

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
app.include_router(research_agent_router, prefix="/api")
app.include_router(sheet_agent_router, prefix="/api")
app.include_router(tictactoe_router, prefix="/api")
app.include_router(workflow_router, prefix="/api")
app.include_router(agent_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(research_router, prefix="/api")
app.include_router(agriculture_router, prefix="/api")


@app.on_event("startup")
async def validate_optional_runtime_dependencies() -> None:
    validate_sheet_agent_dependencies()


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
