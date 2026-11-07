"""OWNER-ONLY Tech Engine (Private Tech Command Center backing).

Separate from customer APIs. ALL routes require OWNER (MFA enforced at login).
Customers/technicians get 403 even with valid tokens. Modified APKs cannot
call these — authorization is server-side on role + MFA-enabled account.

Endpoints: engine status, emergency actions, security incidents, diagnostics.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Role, AuditLog, SupportSession, CompatibilityRecord
from app.deps import require_roles, get_current_user, audit

router = APIRouter()
owner_only = require_roles("OWNER")


@router.get("/status")
async def engine_status(db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar() or 0
    compat_total = (await db.execute(select(func.count()).select_from(CompatibilityRecord))).scalar() or 0
    compat_approved = (await db.execute(select(func.count()).select_from(CompatibilityRecord).where(CompatibilityRecord.is_approved == True))).scalar() or 0
    active_sessions = (await db.execute(select(func.count()).select_from(SupportSession).where(SupportSession.status == "ACTIVE"))).scalar() or 0
    return {
        "engine": "online",
        "total_users": total_users,
        "compat_total": compat_total,
        "compat_approved": compat_approved,
        "active_sessions": active_sessions,
        "owner_email": user.email,
        "note": "Owner-only surface. Customer APK has no route here and cannot reach this router.",
    }


@router.post("/emergency/disable-method")
async def disable_method(body: dict, request: Request, db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    method = str(body.get("method", "")).strip()
    if not method:
        raise HTTPException(400, "method required")
    result = await db.execute(select(CompatibilityRecord).where(CompatibilityRecord.supported_method == method))
    records = result.scalars().all()
    for r in records:
        r.root_eligible = False
        if r.root_classification == "ROOTABLE":
            r.root_classification = "UNKNOWN"
    audit(db, user.id, "ENGINE_DISABLE_METHOD", "root_method", method, request.client.host)
    await db.commit()
    return {"method": method, "disabled_records": len(records)}


@router.post("/emergency/suspend-user")
async def suspend_user(body: dict, request: Request, db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    import uuid
    try:
        uid = uuid.UUID(body["user_id"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(400, "user_id required")
    u = (await db.execute(select(User).where(User.id == uid))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "User not found")
    if u.role == "OWNER":
        raise HTTPException(400, "Cannot suspend owner")
    u.is_active = False
    u.locked_until = None
    audit(db, user.id, "ENGINE_SUSPEND_USER", "user", u.id, request.client.host)
    await db.commit()
    return {"id": str(u.id), "is_active": u.is_active}


@router.post("/emergency/end-sessions")
async def end_all_sessions(request: Request, db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    result = await db.execute(select(SupportSession).where(SupportSession.status == "ACTIVE"))
    sessions = result.scalars().all()
    for s in sessions:
        s.status = "ENDED"
    audit(db, user.id, "ENGINE_END_SESSIONS", "session", f"{len(sessions)}", request.client.host)
    await db.commit()
    return {"ended": len(sessions)}


@router.get("/incidents")
async def incidents(limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    """Security incidents = failed auth + engine actions from audit."""
    result = await db.execute(
        select(AuditLog).where(AuditLog.action.in_(["LOGIN_FAIL", "ACCOUNT_LOCKED", "ENGINE_DISABLE_METHOD", "MFA_DISABLE", "PAYMENT_WEBHOOK_UNKNOWN_REF"]))
        .order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    )
    return [{"id": str(a.id), "action": a.action, "actor": str(a.actor_id) if a.actor_id else None,
             "target": a.target_id, "at": str(a.created_at)} for a in result.scalars()]


@router.get("/diagnostics")
async def diagnostics(db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    return {
        "compat_by_class": {
            cls: (await db.execute(select(func.count()).select_from(CompatibilityRecord).where(CompatibilityRecord.root_classification == cls))).scalar() or 0
            for cls in ["ROOTABLE", "NOT_ROOTABLE", "UNKNOWN", "EXCLUDED"]
        },
        "now": datetime.utcnow().isoformat(),
    }
