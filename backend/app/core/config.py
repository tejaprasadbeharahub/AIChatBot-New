from functools import lru_cache
import json
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    secret_key: Optional[str] = None
    jwt_expire_minutes: int = 480
    jwt_secret_key: Optional[str] = None
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    app_name: Optional[str] = None
    environment: Optional[str] = None

    database_url: Optional[str] = None
    supabase_database_url: Optional[str] = None

    litellm_proxy_url: Optional[str] = None
    litellm_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    google_generative_ai_key: Optional[str] = None
    llm_model: Optional[str] = None
    litellm_embedding_model: Optional[str] = None
    image_gen_model: Optional[str] = None

    google_client_id: Optional[str] = None
    vite_google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    google_service_account_json: Optional[str] = None

    chroma_api_key: Optional[str] = None
    chroma_tenant_id: Optional[str] = None
    chroma_database: Optional[str] = None
    chroma_host: Optional[str] = None
    chroma_persist_dir: Optional[str] = None
    chat_memory_turns: int = 5

    max_upload_mb: int = 20
    upload_dir: Optional[str] = None

    image_gen_max_per_chat: int = 10
    image_gen_max_per_day: int = 50
    image_gen_timeout_seconds: int = 120
    image_storage_dir: Optional[str] = None

    rag_chunk_size: int = 1200
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_embedding_batch_size: int = 32
    rag_max_chunks_per_document: int = 2000

    sql_connection_encryption_key: Optional[str] = None
    sql_default_row_limit: int = 100
    sql_max_row_limit: int = 500
    sql_query_timeout_seconds: int = 30
    sql_generation_temperature: float = 0.0
    sql_generation_model: Optional[str] = None
    sql_generation_retry_count: int = 1

    # Research Agent
    research_max_papers: int = 20
    research_timeout_seconds: int = 120
    research_default_depth: str = "balanced"  # quick, balanced, deep
    arxiv_max_retry_attempts: int = 4
    arxiv_initial_retry_delay_seconds: float = 1.0
    arxiv_max_backoff_delay_seconds: float = 20.0
    arxiv_request_timeout_seconds: int = 12
    arxiv_min_request_interval_seconds: float = 0.4

    # MCP Integration
    mcp_transport: str = "inprocess"  # inprocess | stdio | http | websocket
    mcp_http_url: Optional[str] = None
    mcp_ws_url: Optional[str] = None
    mcp_stdio_command: Optional[str] = None
    mcp_auth_token: Optional[str] = None
    mcp_request_timeout_seconds: int = 20
    mcp_retry_attempts: int = 2
    mcp_retry_backoff_seconds: float = 0.5

    # N8N Workflow Integration
    n8n_workflow_webhook_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("N8N_WEBHOOK_URL", "N8N_WORKFLOW_WEBHOOK_URL"),
    )
    n8n_workflow_timeout_seconds: int = 15
    n8n_classification_model: Optional[str] = None
    n8n_classification_timeout_seconds: int = 15
    n8n_classification_retry_attempts: int = 3
    n8n_classification_enable_fallback: bool = True

    cors_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    cors_allow_credentials: bool = False
    cors_allowed_methods: str = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
    cors_allowed_headers: str = "Content-Type,Authorization"

    def cors_allowed_origins_list(self) -> list[str]:
        raw = (self.cors_allowed_origins or "").strip()
        if not raw:
            return ["http://localhost:5173"]

        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass

        return [item.strip() for item in raw.split(",") if item.strip()]

    def cors_allowed_methods_list(self) -> list[str]:
        raw = (self.cors_allowed_methods or "").strip()
        if not raw:
            return ["GET", "POST", "OPTIONS"]
        return [item.strip().upper() for item in raw.split(",") if item.strip()]

    def cors_allowed_headers_list(self) -> list[str]:
        raw = (self.cors_allowed_headers or "").strip()
        if not raw:
            return ["*"]
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
