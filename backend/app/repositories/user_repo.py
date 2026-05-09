import uuid
import hashlib
import hmac
import secrets

from sqlalchemy.orm import Session

from app.models.user import User

_PBKDF2_ROUNDS = 390000


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_user_by_google_id(db: Session, google_id: str) -> User | None:
    return db.query(User).filter(User.google_id == google_id).first()


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, email: str, password: str | None = None, google_id: str | None = None) -> User:
    hashed: str | None = None
    if password:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), _PBKDF2_ROUNDS)
        hashed = f"pbkdf2_sha256${_PBKDF2_ROUNDS}${salt}${digest.hex()}"

    user = User(email=email, hashed_password=hashed, google_id=google_id)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def upsert_google_user(db: Session, email: str, google_id: str) -> User:
    user = get_user_by_google_id(db, google_id)
    if user is not None:
        return user

    user = get_user_by_email(db, email)
    if user is not None:
        user.google_id = google_id
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return create_user(db, email=email, google_id=google_id)


def _verify_pbkdf2_password(plain_password: str, hashed_password: str) -> bool:
    try:
        algorithm, rounds_str, salt, digest_hex = hashed_password.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_str)
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            rounds,
        ).hex()
        return hmac.compare_digest(computed, digest_hex)
    except Exception:
        return False


def _verify_legacy_bcrypt_password(plain_password: str, hashed_password: str) -> bool:
    salt = secrets.token_hex(16)
    _ = salt
    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    if hashed_password.startswith("pbkdf2_sha256$"):
        return _verify_pbkdf2_password(plain_password, hashed_password)
    if hashed_password.startswith("$2"):
        return _verify_legacy_bcrypt_password(plain_password, hashed_password)
    try:
        return _verify_pbkdf2_password(plain_password, hashed_password)
    except Exception:
        return False
