"""JWT + password hashing. Never log raw passwords/tokens."""
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def hash_password(raw: str) -> str:
    return pwd.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    return pwd.verify(raw, hashed)


def create_access_token(subject: str, role: str) -> str:
    payload = {
        "sub": subject,
        "role": role,
        "exp": datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    payload = {
        "sub": subject,
        "exp": datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
