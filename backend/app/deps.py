"""Auth + RBAC dependencies. Server-side authorization only."""
import uuid
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Role
from app.security import decode_token

bearer = HTTPBearer(auto_error=False)

PRIVILEGED = {Role.OWNER, Role.SUPER_ADMIN, Role.ADMIN}


async def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not creds:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        payload = decode_token(creds.credentials)
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token type")
    try:
        user_uuid = uuid.UUID(str(payload["sub"]))
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid subject")
    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or inactive")
    return user


def require_roles(*roles: str):
    async def guard(user: User = Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient permissions")
        return user
    return guard


def audit(db: AsyncSession, actor_id, action, target_type="", target_id="", ip="", meta=None):
    """Callers commit the session after this."""
    from app.models import AuditLog
    db.add(AuditLog(actor_id=actor_id, action=action, target_type=target_type,
                    target_id=str(target_id), ip=ip, meta=meta or {}))
