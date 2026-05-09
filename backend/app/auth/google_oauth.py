from dataclasses import dataclass

from google.auth.transport import requests
from google.oauth2 import id_token

from app.core.config import settings


GOOGLE_TOKEN_CLOCK_SKEW_SECONDS = 10


@dataclass
class GoogleIdentity:
    google_id: str
    email: str
    email_verified: bool


def verify_google_token(token: str) -> GoogleIdentity:
    allowed_audiences = {
        value.strip()
        for value in [settings.google_client_id, settings.vite_google_client_id]
        if value and value.strip()
    }

    if not allowed_audiences:
        raise ValueError("GOOGLE_CLIENT_ID or VITE_GOOGLE_CLIENT_ID is not configured")

    try:
        # Verify signature/issuer/expiry first, then validate audience against configured client ids.
        payload = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            clock_skew_in_seconds=GOOGLE_TOKEN_CLOCK_SKEW_SECONDS,
        )
    except Exception as exc:
        raise ValueError(f"Invalid Google token: {exc}") from exc

    audience = payload.get("aud")
    if audience not in allowed_audiences:
        raise ValueError(
            f"Google token audience mismatch: got '{audience}', expected one of {sorted(allowed_audiences)}"
        )

    google_id = payload.get("sub")
    email = payload.get("email")
    email_verified = bool(payload.get("email_verified"))

    if not google_id or not email:
        raise ValueError("Google token is missing required claims")
    if not email_verified:
        raise ValueError("Google email is not verified")

    return GoogleIdentity(google_id=google_id, email=email.lower().strip(), email_verified=email_verified)
