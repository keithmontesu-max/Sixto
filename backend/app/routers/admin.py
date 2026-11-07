"""Admin Command Center API (System B backing). Real data only, date-filtered."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import User, Device, Order, Payment, SupportSession, AuditLog
from app.deps import require_roles

router = APIRouter()
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")


@router.get("/overview")
async def overview(range: str = "7d", db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    days = {"today": 0, "yesterday": 1, "7d": 7, "30d": 30, "90d": 90}.get(range, 7)
    since = datetime.utcnow() - timedelta(days=days) if days else datetime.utcnow().replace(hour=0, minute=0, second=0)

    async def count(model, *conds):
        q = select(func.count()).select_from(model)
        for c in conds:
            q = q.where(c)
        return (await db.execute(q)).scalar() or 0

    total_customers = await count(User, User.role == "CUSTOMER")
    new_customers = await count(User, User.created_at >= since)
    registered_devices = await count(Device)
    total_orders = await count(Order, Order.created_at >= since)
    completed_orders = await count(Order, Order.created_at >= since, Order.status == "COMPLETED")
    failed_orders = await count(Order, Order.created_at >= since, Order.status == "FAILED")
    gross_revenue = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
            Payment.status == "PAID", Payment.created_at >= since)
    )).scalar() or 0
    refunds = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount_cents), 0)).where(
            Payment.status == "REFUNDED", Payment.created_at >= since)
    )).scalar() or 0
    active_sessions = await count(SupportSession, SupportSession.status == "ACTIVE")

    return {
        "range": range,
        "total_customers": total_customers,
        "new_customers": new_customers,
        "registered_devices": registered_devices,
        "active_technicians": await count(User, User.role == "TECHNICIAN", User.is_active == True),
        "total_orders": total_orders,
        "completed_orders": completed_orders,
        "failed_orders": failed_orders,
        "gross_revenue_cents": gross_revenue,
        "refunds_cents": refunds,
        "net_revenue_cents": gross_revenue - refunds,
        "active_sessions": active_sessions,
    }


@router.get("/audit")
async def audit_feed(limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(min(limit, 500))
    )
    return [{"id": str(a.id), "actor_id": str(a.actor_id) if a.actor_id else None,
             "action": a.action, "target_type": a.target_type, "target_id": a.target_id,
             "created_at": str(a.created_at)} for a in result.scalars()]


@router.get("/customers")
async def customers(q: str = "", limit: int = 50, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    stmt = select(User).where(User.role == "CUSTOMER")
    if q:
        stmt = stmt.where(User.email.ilike(f"%{q}%"))
    result = await db.execute(stmt.limit(min(limit, 200)))
    return [{"id": str(u.id), "email": u.email, "full_name": u.full_name,
             "is_active": u.is_active, "created_at": str(u.created_at)} for u in result.scalars()]


@router.get("/orders")
async def all_orders(status: str = "", limit: int = 100, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    stmt = select(Order).order_by(Order.created_at.desc())
    if status:
        stmt = stmt.where(Order.status == status.upper())
    result = await db.execute(stmt.limit(min(limit, 500)))
    return [
        {"id": str(o.id), "user_id": str(o.user_id), "status": o.status,
         "total_cents": o.total_cents, "currency": o.currency,
         "technician": str(o.technician_id) if o.technician_id else None,
         "timeline": o.timeline, "created_at": str(o.created_at)}
        for o in result.scalars()
    ]


@router.get("/payments/pending")
async def pending_payments(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(Payment).where(Payment.status == "PENDING").order_by(Payment.created_at.desc()))
    return [
        {"id": str(p.id), "order_id": str(p.order_id), "provider": p.provider,
         "provider_ref": p.provider_ref, "amount_cents": p.amount_cents, "created_at": str(p.created_at)}
        for p in result.scalars()
    ]
