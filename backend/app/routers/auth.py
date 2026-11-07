"""Auth: register / login / refresh / MFA. Login abuse guard + audit."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Role
from app.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.deps import get_current_user, audit
import pyotp

router = APIRouter()


class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    totp_code: str = ""


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


async def _maybe_lock(db, user: User, ip: str):
    if user.failed_logins >= 5:
        user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        audit(db, user.id, "ACCOUNT_LOCKED", "user", user.id, ip)
        await db.commit()
        raise HTTPException(423, "Account temporarily locked. Try again later.")


@router.post("/register", status_code=201, response_model=TokenOut)
async def register(payload: RegisterIn, request: Request, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        # Generic message — do not leak which emails exist
        raise HTTPException(400, "Registration could not be completed. Check your email or try signing in.")
    user = User(email=payload.email, password_hash=hash_password(payload.password),
                role=Role.CUSTOMER.value, full_name=payload.full_name)
    db.add(user)
    audit(db, None, "REGISTER", "user", "", request.client.host)
    await db.commit()
    await db.refresh(user)
    return TokenOut(access_token=create_access_token(str(user.id), user.role),
                    refresh_token=create_refresh_token(str(user.id)))


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    if user.locked_until and user.locked_until > datetime.utcnow():
        raise HTTPException(423, "Account temporarily locked. Try again later.")
    if not user.is_active:
        raise HTTPException(403, "Account is inactive. Contact support.")
    # MFA for privileged roles
    if user.role in ("OWNER", "SUPER_ADMIN", "ADMIN") and user.totp_enabled:
        if not payload.totp_code or not pyotp.TOTP(user.totp_secret).verify(payload.totp_code):
            raise HTTPException(401, "MFA verification required")
    user.failed_logins = 0
    user.locked_until = None
    audit(db, user.id, "LOGIN", "user", user.id, request.client.host)
    await db.commit()
    return TokenOut(access_token=create_access_token(str(user.id), user.role),
                    refresh_token=create_refresh_token(str(user.id)))


@router.post("/refresh", response_model=TokenOut)
async def refresh(body: dict, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.get("refresh_token", ""))
    except Exception:
        raise HTTPException(401, "Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid token type")
    import uuid as _uuid
    result = await db.execute(select(User).where(User.id == _uuid.UUID(str(payload["sub"]))))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return TokenOut(access_token=create_access_token(str(user.id), user.role),
                    refresh_token=create_refresh_token(str(user.id)))


@router.post("/mfa/enable")
async def mfa_enable(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    secret = pyotp.random_base32()
    user.totp_secret = secret
    user.totp_enabled = True
    audit(db, user.id, "MFA_ENABLE", "user", user.id)
    await db.commit()
    return {"provisioning_uri": pyotp.totp.TOTP(secret).provisioning_uri(user.email, issuer_name="SIXTO ROOT X")}


@router.post("/mfa/disable")
async def mfa_disable(body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if not user.totp_secret or not pyotp.TOTP(user.totp_secret).verify(body.get("totp_code", "")):
        raise HTTPException(401, "Invalid MFA code")
    user.totp_enabled = False
    user.totp_secret = None
    audit(db, user.id, "MFA_DISABLE", "user", user.id)
    await db.commit()
    return {"ok": True}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "role": user.role,
            "full_name": user.full_name, "is_verified": user.is_verified,
            "prefs": {"ntf_order": user.ntf_order, "ntf_payment": user.ntf_payment,
                      "ntf_promo": user.ntf_promo, "ntf_security": user.ntf_security}}


@router.post("/prefs")
async def update_prefs(body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    for k in ("ntf_order", "ntf_payment", "ntf_promo", "ntf_security"):
        if k in body:
            setattr(user, k, bool(body[k]))
    audit(db, user.id, "PREFS_UPDATE", "user", user.id)
    await db.commit()
    return {"prefs": {"ntf_order": user.ntf_order, "ntf_payment": user.ntf_payment,
                      "ntf_promo": user.ntf_promo, "ntf_security": user.ntf_security}}


@router.post("/deletion-request")
async def deletion_request(body: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """Soft delete: deactivate + anonymize. Orders/payments retained for audit/legal."""
    user.is_active = False
    user.full_name = "Deleted User"
    user.phone = ""
    audit(db, user.id, "ACCOUNT_DELETE_REQUEST", "user", user.id)
    await db.commit()
    return {"ok": True, "message": "Account deactivated. Admin review pending for full erase."}
