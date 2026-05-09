from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings
from app.schemas.user import TokenData

ALGORITHM = settings.jwt_algorithm or "HS256"


def _secret() -> str:
    if not settings.jwt_secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured. Set it in .env.")
    return settings.jwt_secret_key


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes or 60)
    )
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    return jwt.encode(payload, _secret(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, _secret(), algorithms=[ALGORITHM])
        sub: str | None = payload.get("sub")
        if sub is None:
            raise ValueError("Token missing subject claim")
        return TokenData(sub=sub)
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
