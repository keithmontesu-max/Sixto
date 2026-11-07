"""Automation engine — safe, auditable rules only.

Rules: auto-assign by availability, notify on status change, escalate overdue,
payment confirmation, completion reports, failure alerts, demand stats.
Sensitive finance/destructive actions are NEVER automated. Every run audits.

GET  /automation/rules         (admin)
POST /automation/run/assign    (admin — assigns PAYMENT_CONFIRMED orders to idle technicians)
POST /automation/run/notify    (admin — sends pending notifications + escalates stale orders)
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Order, User, Role, Notification
from app.deps import require_roles, audit

router = APIRouter()
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")

RULES = {
    "auto_assign": "Assign PAYMENT_CONFIRMED orders to least-busy active technician",
    "notify_on_status": "Notify customer on every order status change (via timeline emit)",
    "escalate_overdue": "Flag PAYMENT_CONFIRMED orders older than 24h without technician",
    "payment_confirm": "Emit notification after server-verified payment (handled in webhook)",
    "completion_report": "Emit notification + report link on COMPLETED",
    "failure_alert": "Alert admins when failed rate exceeds threshold (manual review here)",
}


@router.get("/rules")
async def rules(user=Depends(admin_only)):
    return {"rules": [{"name": k, "description": v} for k, v in RULES.items()]}


@router.post("/run/assign")
async def run_assign(request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    orders = (await db.execute(select(Order).where(Order.status == "PAYMENT_CONFIRMED"))).scalars().all()
    techs = (await db.execute(select(User).where(User.role == "TECHNICIAN", User.is_active == True))).scalars().all()
    if not orders or not techs:
        return {"assigned": 0, "message": "Nothing to assign"}
    assigned = 0
    for o in orders:
        counts = {}
        for t in techs:
            active = (await db.execute(select(Order).where(Order.technician_id == t.id, Order.status.in_(["TECHNICIAN_ASSIGNED", "IN_PROGRESS"])))).scalars().all()
            counts[str(t.id)] = len(active)
        chosen = sorted(counts, key=counts.get)[0]
        o.technician_id = chosen
        o.status = "TECHNICIAN_ASSIGNED"
        o.timeline = [*o.timeline, {"status": "TECHNICIAN_ASSIGNED", "note": "Auto-assigned"}]
        db.add(Notification(user_id=o.user_id, title="Technician assigned", body=f"Order {str(o.id)[:8]} has a technician.", kind="order"))
        assigned += 1
    audit(db, user.id, "AUTOMATION_ASSIGN", "order", "", request.client.host, {"assigned": assigned})
    await db.commit()
    return {"assigned": assigned}


@router.post("/run/notify")
async def run_notify(request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    cutoff = datetime.utcnow() - timedelta(hours=24)
    stale = (await db.execute(select(Order).where(Order.status == "PAYMENT_CONFIRMED", Order.created_at < cutoff))).scalars().all()
    admins = (await db.execute(select(User).where(User.role.in_(["OWNER", "SUPER_ADMIN", "ADMIN"]), User.is_active == True))).scalars().all()
    for o in stale:
        for a in admins:
            db.add(Notification(user_id=a.id, title="Overdue order", body=f"Order {str(o.id)[:8]} awaiting technician >24h.", kind="order"))
    audit(db, user.id, "AUTOMATION_NOTIFY", "order", "", request.client.host, {"stale": len(stale)})
    await db.commit()
    return {"escalated": len(stale)}
