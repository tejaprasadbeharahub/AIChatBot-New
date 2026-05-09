from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import attachment as _attachment_model  # noqa: F401
from app.models import chat as _chat_model  # noqa: F401
from app.models import message as _message_model  # noqa: F401
from app.models import user as _user_model  # noqa: F401
from app.models import generated_image as _generated_image_model  # noqa: F401
from app.models import pdf_document as _pdf_document_model  # noqa: F401


def _make_engine():
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Add it to .env before starting the server.")
    return create_engine(url, pool_pre_ping=True, future=True)


@lru_cache(maxsize=1)
def _engine():
    return _make_engine()


@lru_cache(maxsize=1)
def _make_session_factory():
    return sessionmaker(autocommit=False, autoflush=False, bind=_engine())


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy session and closes it after the request."""
    db = _make_session_factory()()
    try:
        yield db
    finally:
        db.close()
