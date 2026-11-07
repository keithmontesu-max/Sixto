"""Secure remote support session pairing (QR + codes). No device control here —
local operations run only via allowlisted on-device operations with customer consent."""
import secrets
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import SupportSession, Order
from app.deps import get_current_user, require_roles

router = APIRouter()


def _new_code():
    return secrets.token_hex(4).upper()  # 8-char session code


@router.post("", status_code=201)
async def create_session(body: dict, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    order_id_raw = body.get("order_id")
    order_id = None
    if order_id_raw:
        try:
            order_id = uuid.UUID(str(order_id_raw))
        except (ValueError, TypeError):
            raise HTTPException(404, "Order not found")
        o = await db.execute(select(Order).where(Order.id == order_id, Order.user_id == user.id))
        if not o.scalar_one_or_none():
            raise HTTPException(404, "Order not found")
    session = SupportSession(order_id=order_id, customer_id=user.id, code=_new_code(),
                             status="WAITING", expires_at=datetime.utcnow() + timedelta(minutes=20))
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {"id": str(session.id), "code": session.code, "status": session.status,
            "expires_at": str(session.expires_at), "pairing_hint": "Technician enters this code or scans QR"}


@router.get("/{code}")
async def session_status(code: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(SupportSession).where(SupportSession.code == code.upper()))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Session not found")
    if session_expired(s):
        s.status = "EXPIRED"
        await db.commit()
    return {"id": str(s.id), "status": s.status, "expires_at": str(s.expires_at)}


def session_expired(s: SupportSession) -> bool:
    return bool(s.expires_at and s.expires_at < datetime.utcnow() and s.status in ("WAITING", "ACTIVE"))


@router.post("/join")
async def join_session(body: dict, db: AsyncSession = Depends(get_db), user=Depends(require_roles("TECHNICIAN", "ADMIN", "SUPER_ADMIN", "OWNER"))):
    code = (body.get("code") or "").upper()
    result = await db.execute(select(SupportSession).where(SupportSession.code == code))
    s = result.scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Session not found")
    if session_expired(s):
        raise HTTPException(410, "Session expired")
    s.technician_id = user.id
    s.status = "ACTIVE"
    await db.commit()
    return {"id": str(s.id), "status": s.status, "customer_id": str(s.customer_id)}
