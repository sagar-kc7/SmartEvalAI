"""Password hashing and JWT token utilities."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from smartevalai.core.config import get_settings

settings = get_settings()

JWT_ALGORITHM = "HS256"


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage.

    bcrypt has a hard 72-byte input limit, so we truncate defensively —
    in practice no real password should ever hit this limit.
    """
    password_bytes = plain_password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against its stored hash."""
    password_bytes = plain_password.encode("utf-8")[:72]
    return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))


def create_access_token(subject: str, role: str) -> str:
    """Create a signed JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises:
        jwt.PyJWTError: If the token is invalid, malformed, or expired.
    """
    return jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])