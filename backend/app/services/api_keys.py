import hashlib
import secrets
from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.models import ApiKey, User, utc_now

PREFIX = "osnsk_"


def generate_api_key() -> str:
    return PREFIX + secrets.token_hex(20)


def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def validate_api_key(key: str, session: Session) -> User | None:
    if not key.startswith(PREFIX):
        return None

    key_hash = hash_api_key(key)
    key_prefix = key[:8]

    statement = select(ApiKey).where(
        ApiKey.key_prefix == key_prefix,
        ApiKey.key_hash == key_hash,
        ApiKey.is_active == True,  # noqa: E712
    )
    api_key = session.exec(statement).first()
    if api_key is None:
        return None

    if api_key.expires_at is not None:
        expires = api_key.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=UTC)
        if expires < datetime.now(tz=UTC):
            return None

    api_key.last_used_at = utc_now()
    session.add(api_key)
    session.commit()

    return api_key.user
