from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.config import settings

# Using bcrypt directly instead of passlib's CryptContext: passlib 1.7.4's
# backend detection reads bcrypt.__about__.__version__, which was removed in
# bcrypt>=4.1, causing a hard crash on hash(). Direct bcrypt calls sidestep
# that whole fragile version-detection path.
BCRYPT_MAX_BYTES = 72


def hash_password(password: str) -> str:
    pw_bytes = password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw_bytes = plain_password.encode("utf-8")[:BCRYPT_MAX_BYTES]
    return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))


def create_token(data: dict, expires_delta: timedelta, token_type: str = "access") -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(subject: str, role: str) -> str:
    return create_token(
        {"sub": subject, "role": role},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "access",
    )


def create_refresh_token(subject: str, role: str) -> str:
    return create_token(
        {"sub": subject, "role": role},
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "refresh",
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
