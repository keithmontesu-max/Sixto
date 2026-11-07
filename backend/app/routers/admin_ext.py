"""Admin extensions: technicians, releases, bugs, finance breakdown, config.

All ADMIN/OWNER-only. Technician accounts are User rows with role=TECHNICIAN.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Role, AppRelease, BugReport, BusinessConfig, Payment, Order, Device, SupportSession
from app.deps import get_current_user, require_roles, audit
from app.security import hash_password

router = APIRouter()
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")


# --- Technicians ---

class TechIn(BaseModel):
    email: str
    password: str
    full_name: str = ""


@router.get("/technicians")
async def technicians(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(User).where(User.role == "TECHNICIAN"))
    return [{"id": str(u.id), "email": u.email, "full_name": u.full_name, "is_active": u.is_active,
             "created_at": str(u.created_at)} for u in result.scalars()]


@router.post("/technicians", status_code=201)
async def create_technician(payload: TechIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    ex = await db.execute(select(User).where(User.email == payload.email))
    if ex.scalar_one_or_none():
        raise HTTPException(400, "Email already in use")
    t = User(email=payload.email, password_hash=hash_password(payload.password),
             role=Role.TECHNICIAN.value, full_name=payload.full_name)
    db.add(t)
    audit(db, user.id, "TECH_CREATE", "user", t.id, request.client.host)
    await db.commit()
    await db.refresh(t)
    return {"id": str(t.id), "email": t.email}


@router.post("/technicians/{user_id}/toggle")
async def toggle_technician(user_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    try:
        uid = uuid.UUID(user_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "User not found")
    t = (await db.execute(select(User).where(User.id == uid, User.role == "TECHNICIAN"))).scalar_one_or_none()
    if not t:
        raise HTTPException(404, "Technician not found")
    t.is_active = not t.is_active
    audit(db, user.id, "TECH_TOGGLE", "user", t.id, request.client.host, {"active": t.is_active})
    await db.commit()
    return {"id": str(t.id), "is_active": t.is_active}


@router.post("/assign")
async def assign_order(body: dict, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    """Assign order → technician (M5 auto-assign rule lives in automation.py; this is manual)."""
    try:
        oid = uuid.UUID(body["order_id"])
        tid = uuid.UUID(body["technician_id"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(400, "order_id and technician_id required")
    o = (await db.execute(select(Order).where(Order.id == oid))).scalar_one_or_none()
    t = (await db.execute(select(User).where(User.id == tid, User.role == "TECHNICIAN", User.is_active == True))).scalar_one_or_none()
    if not o or not t:
        raise HTTPException(404, "Order or technician not found")
    o.technician_id = tid
    o.status = "TECHNICIAN_ASSIGNED"
    o.timeline = [*o.timeline, {"status": "TECHNICIAN_ASSIGNED", "note": t.email}]
    audit(db, user.id, "ORDER_ASSIGN", "order", o.id, request.client.host, {"technician": str(tid)})
    await db.commit()
    return {"id": str(o.id), "status": o.status, "technician": str(tid)}


# --- Releases ---

class ReleaseIn(BaseModel):
    channel: str = "android"
    version: str
    notes: str = ""
    signature_hash: str = ""
    rollout_percent: int = 100


@router.get("/releases")
async def releases(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(AppRelease).order_by(AppRelease.created_at.desc()).limit(50))
    return [{"id": str(r.id), "channel": r.channel, "version": r.version, "notes": r.notes,
             "signature_hash": r.signature_hash, "is_active": r.is_active,
             "rollout_percent": r.rollout_percent, "created_at": str(r.created_at)} for r in result.scalars()]


@router.post("/releases", status_code=201)
async def create_release(payload: ReleaseIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    # Deactivate others in channel (one active release per channel).
    prev = await db.execute(select(AppRelease).where(AppRelease.channel == payload.channel, AppRelease.is_active == True))
    for r in prev.scalars():
        r.is_active = False
    rel = AppRelease(**payload.model_dump(), is_active=True)
    db.add(rel)
    audit(db, user.id, "RELEASE_PUBLISH", "release", rel.id, request.client.host, {"channel": payload.channel, "version": payload.version})
    await db.commit()
    await db.refresh(rel)
    return {"id": str(rel.id), "version": rel.version}


@router.get("/releases/active")
async def active_release(channel: str = "android", db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    r = (await db.execute(select(AppRelease).where(AppRelease.channel == channel, AppRelease.is_active == True))).scalar_one_or_none()
    if not r:
        return {"active": False}
    return {"active": True, "version": r.version, "notes": r.notes, "signature_hash": r.signature_hash, "rollout_percent": r.rollout_percent}


# --- Bugs ---

class BugIn(BaseModel):
    title: str
    description: str = ""
    severity: str = "LOW"
    device_id: str = ""


@router.get("/bugs")
async def bugs(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(BugReport).order_by(BugReport.created_at.desc()).limit(100))
    return [{"id": str(b.id), "title": b.title, "severity": b.severity, "status": b.status,
             "device_id": str(b.device_id) if b.device_id else None, "created_at": str(b.created_at)} for b in result.scalars()]


@router.post("/bugs", status_code=201)
async def create_bug(payload: BugIn, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    dev_id = None
    if payload.device_id:
        try:
            dev_id = uuid.UUID(payload.device_id)
        except (ValueError, TypeError):
            raise HTTPException(400, "Invalid device_id")
    b = BugReport(reporter_id=user.id, device_id=dev_id, title=payload.title,
                  description=payload.description, severity=payload.severity.upper())
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return {"id": str(b.id), "title": b.title}


@router.post("/bugs/{bug_id}/status")
async def bug_status(bug_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    try:
        bid = uuid.UUID(bug_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Bug not found")
    b = (await db.execute(select(BugReport).where(BugReport.id == bid))).scalar_one_or_none()
    if not b:
        raise HTTPException(404, "Bug not found")
    b.status = str(body.get("status", b.status)).upper()
    audit(db, user.id, "BUG_STATUS", "bug", b.id, request.client.host, {"status": b.status})
    await db.commit()
    return {"id": str(b.id), "status": b.status}


# --- Finance breakdown ---

@router.get("/finance")
async def finance(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    gross = (await db.execute(select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(Payment.status == "PAID"))).scalar() or 0
    refunds = (await db.execute(select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(Payment.status == "REFUNDED"))).scalar() or 0
    pending = (await db.execute(select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(Payment.status == "PENDING"))).scalar() or 0
    orders = (await db.execute(select(func.count()).select_from(Order))).scalar() or 0
    aov = (gross / orders) if orders else 0
    return {"gross_cents": gross, "refunds_cents": refunds, "net_cents": gross - refunds,
            "pending_cents": pending, "orders": orders, "avg_order_value_cents": aov}


@router.get("/finance/export")
async def finance_export(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    """CSV of verified payments (PAID/REFUNDED) for owner records."""
    from fastapi.responses import Response
    result = await db.execute(select(Payment).where(Payment.status.in_(["PAID", "REFUNDED"])).order_by(Payment.created_at))
    lines = ["id,order_id,provider,ref,amount_cents,currency,status,created_at"]
    for p in result.scalars():
        lines.append(f"{p.id},{p.order_id},{p.provider},{p.provider_ref},{p.amount_cents},{p.currency},{p.status},{p.created_at}")
    csv_body = "\n".join(lines)
    return Response(content=csv_body, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=sixto-finance.csv"})


# --- Business config ---

class ConfigIn(BaseModel):
    key: str
    value: dict


@router.get("/config")
async def config_list(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(BusinessConfig))
    return [{"key": c.key, "value": c.value} for c in result.scalars()]


@router.post("/config")
async def config_upsert(payload: ConfigIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    existing = await db.execute(select(BusinessConfig).where(BusinessConfig.key == payload.key))
    c = existing.scalar_one_or_none()
    if c:
        c.value = payload.value
    else:
        c = BusinessConfig(key=payload.key, value=payload.value)
        db.add(c)
    audit(db, user.id, "CONFIG_UPSERT", "business_config", payload.key, request.client.host)
    await db.commit()
    return {"key": payload.key}
