"""Push token registration — FCM tokens mirrored for best-effort delivery.

In-app notifications are the source of truth; push is a mirror.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import PushToken
from app.deps import get_current_user

router = APIRouter()


class TokenIn(BaseModel):
    token: str
    platform: str = "android"


@router.post("/register")
async def register_token(payload: TokenIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if not (payload.token or "").strip():
        raise HTTPException(400, "token required")
    existing = (await db.execute(select(PushToken).where(PushToken.token == payload.token))).scalar_one_or_none()
    if existing:
        existing.user_id = user.id
    else:
        db.add(PushToken(user_id=user.id, token=payload.token, platform=payload.platform))
    await db.commit()
    return {"ok": True}


@router.get("/mine")
async def mine(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(PushToken).where(PushToken.user_id == user.id))
    return [{"token": t.token, "platform": t.platform} for t in result.scalars()]
