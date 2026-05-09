from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


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
