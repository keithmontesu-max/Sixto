"""Remote support: session history + REST message fallback + WebSocket live relay.

WebSocket: /api/v1/remote/sessions/ws/{code}?token=JWT
  - Auth via query token (browser clients can't set headers on WS reliably).
  - Each connection is scoped to one session; only customer/technician/admins of it.
  - Protocol: {"kind":"text|status|consent|diag","body":"..."} → persisted + broadcast.
  - No device control here; on-device ops need separate authorization (operations API).
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db, async_session
from app.models import SupportSession, SessionMessage, User
from app.deps import get_current_user
from app.security import decode_token

router = APIRouter()

# code -> set of websockets
_active: dict[str, list[WebSocket]] = {}


async def _async_user_from_token(token: str) -> User | None:
    try:
        payload = decode_token(token)
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    async with async_session() as db:
        try:
            uid = uuid.UUID(str(payload["sub"]))
        except Exception:
            return None
        u = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
        return u


@router.get("/sessions/mine")
async def my_sessions(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(SupportSession).where(SupportSession.customer_id == user.id).order_by(SupportSession.created_at.desc()))
    return [{"id": str(s.id), "code": s.code, "status": s.status, "created_at": str(s.created_at)} for s in result.scalars()]


@router.get("/sessions/{session_id}/messages")
async def messages(session_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        sid = uuid.UUID(session_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Session not found")
    s = (await db.execute(select(SupportSession).where(SupportSession.id == sid))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Session not found")
    if user.id not in (s.customer_id, s.technician_id) and user.role not in ("OWNER", "SUPER_ADMIN", "ADMIN"):
        raise HTTPException(403, "No access to this session")
    result = await db.execute(select(SessionMessage).where(SessionMessage.session_id == sid).order_by(SessionMessage.created_at))
    return [{"id": str(m.id), "sender_id": str(m.sender_id), "kind": m.kind, "body": m.body, "created_at": str(m.created_at)} for m in result.scalars()]


class MsgIn(BaseModel):
    kind: str = "text"
    body: str


@router.post("/sessions/{session_id}/messages")
async def post_message(session_id: str, payload: MsgIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        sid = uuid.UUID(session_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Session not found")
    s = (await db.execute(select(SupportSession).where(SupportSession.id == sid))).scalar_one_or_none()
    if not s:
        raise HTTPException(404, "Session not found")
    if user.id not in (s.customer_id, s.technician_id) and user.role not in ("OWNER", "SUPER_ADMIN", "ADMIN"):
        raise HTTPException(403, "No access")
    if payload.kind not in ("text", "status", "consent", "diag"):
        raise HTTPException(400, "Invalid kind")
    msg = SessionMessage(session_id=sid, sender_id=user.id, kind=payload.kind, body=payload.body[:4000])
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    await _broadcast(s.code, {"kind": msg.kind, "body": msg.body, "sender_id": str(msg.sender_id)})
    return {"id": str(msg.id), "kind": msg.kind}


async def _broadcast(code: str, payload: dict):
    import json
    for ws in _active.get(code, []):
        try:
            await ws.send_text(json.dumps(payload))
        except Exception:
            pass


@router.websocket("/sessions/ws/{code}")
async def ws_session(ws: WebSocket, code: str, token: str = Query("")):
    user = await _async_user_from_token(token)
    if not user:
        await ws.close(code=1008)
        return
    async with async_session() as db:
        s = (await db.execute(select(SupportSession).where(SupportSession.code == code.upper()))).scalar_one_or_none()
        if not s or user.id not in (s.customer_id, s.technician_id) and user.role not in ("OWNER", "SUPER_ADMIN", "ADMIN"):
            await ws.close(code=1008)
            return
        session_id = s.id
    await ws.accept()
    _active.setdefault(code.upper(), []).append(ws)
    try:
        while True:
            data = await ws.receive_text()
            import json
            try:
                payload = json.loads(data)
            except Exception:
                await ws.send_text(json.dumps({"error": "invalid json"}))
                continue
            kind = payload.get("kind", "text")
            body = str(payload.get("body", ""))[:4000]
            if kind not in ("text", "status", "consent", "diag"):
                await ws.send_text(json.dumps({"error": "invalid kind"}))
                continue
            async with async_session() as db:
                msg = SessionMessage(session_id=session_id, sender_id=user.id, kind=kind, body=body)
                db.add(msg)
                await db.commit()
            await _broadcast(code.upper(), {"kind": kind, "body": body, "sender_id": str(user.id)})
    except WebSocketDisconnect:
        pass
    finally:
        _active.get(code.upper(), []).remove(ws) if ws in _active.get(code.upper(), []) else None
