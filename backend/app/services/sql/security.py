import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _resolve_encryption_key() -> bytes:
    raw_key = (settings.sql_connection_encryption_key or settings.secret_key or settings.jwt_secret_key or "").strip()
    if not raw_key:
        raise ValueError("Missing SQL_CONNECTION_ENCRYPTION_KEY (or SECRET_KEY/JWT_SECRET_KEY fallback).")

    digest = hashlib.sha256(raw_key.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    fernet = Fernet(_resolve_encryption_key())
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_secret(value: str | None) -> str | None:
    if not value:
        return None
    fernet = Fernet(_resolve_encryption_key())
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
