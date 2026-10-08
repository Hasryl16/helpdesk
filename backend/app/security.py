from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.config import settings

ALGORITHM = "HS256"


def _password_bytes(password: str) -> bytes:
    # bcrypt only reads 72 bytes and bcrypt>=5 raises on longer input, so cut it explicitly.
    return password.encode()[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_password_bytes(password), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(_password_bytes(password), password_hash.encode())


def create_token(user_id: int, token_type: str) -> str:
    if token_type == "access":
        lifetime = timedelta(minutes=settings.access_token_minutes)
    else:
        lifetime = timedelta(days=settings.refresh_token_days)
    payload = {"sub": str(user_id), "type": token_type, "exp": datetime.now(timezone.utc) + lifetime}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str) -> int | None:
    """Return the user id from a valid token of the expected type, otherwise None."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != expected_type:
        return None
    return int(payload["sub"])
