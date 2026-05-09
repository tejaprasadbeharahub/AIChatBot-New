from functools import lru_cache
from pathlib import Path
from typing import Optional

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

    litellm_proxy_url: Optional[str] = None
    litellm_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    litellm_embedding_model: Optional[str] = None
    image_gen_model: Optional[str] = None

    google_client_id: Optional[str] = None
    vite_google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_redirect_uri: Optional[str] = None
    google_service_account_json: Optional[str] = None

    chroma_persist_dir: Optional[str] = None

    max_upload_mb: int = 20
    upload_dir: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
