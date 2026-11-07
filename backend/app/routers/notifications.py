"""Notifications — in-app center. Push/email adapters hook in here later.

Events: registration, compat result, order/payment, technician assignment,
session invite, progress, completion, refunds, updates, security alerts.
Customers control non-essential kinds via preferences (stored in BusinessConfig? per-user flag on User later).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Notification
from app.deps import get_current_user

router = APIRouter()


@router.get("/mine")
async def mine(unread_only: bool = False, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    q = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        q = q.where(Notification.is_read == False)
    result = await db.execute(q.order_by(Notification.created_at.desc()).limit(100))
    return [{"id": str(n.id), "title": n.title, "body": n.body, "kind": n.kind,
             "is_read": n.is_read, "created_at": str(n.created_at)} for n in result.scalars()]


@router.post("/{notif_id}/read")
async def mark_read(notif_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    import uuid
    try:
        nid = uuid.UUID(notif_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Not found")
    n = (await db.execute(select(Notification).where(Notification.id == nid, Notification.user_id == user.id))).scalar_one_or_none()
    if not n:
        raise HTTPException(404, "Not found")
    n.is_read = True
    await db.commit()
    return {"ok": True}


async def notify(db: AsyncSession, user_id, title: str, body: str, kind: str = "info") -> None:
    """Internal helper — callers commit."""
    db.add(Notification(user_id=user_id, title=title, body=body, kind=kind))
