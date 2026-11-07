"""Technician portal — assigned orders, session join, completion reports."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Order
from app.deps import get_current_user, require_roles, audit

router = APIRouter()
tech = require_roles("TECHNICIAN", "ADMIN", "SUPER_ADMIN", "OWNER")


@router.get("/my-orders")
async def my_orders(db: AsyncSession = Depends(get_db), user=Depends(tech)):
    result = await db.execute(
        select(Order).where(Order.technician_id == user.id).order_by(Order.created_at.desc()).limit(100)
    )
    return [{"id": str(o.id), "status": o.status, "total_cents": o.total_cents,
             "timeline": o.timeline, "completion_report": o.completion_report,
             "created_at": str(o.created_at)} for o in result.scalars()]


@router.post("/orders/{order_id}/start")
async def start_order(order_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(tech)):
    import uuid
    try:
        oid = uuid.UUID(order_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Order not found")
    o = (await db.execute(select(Order).where(Order.id == oid, Order.technician_id == user.id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Order not found or not assigned to you")
    o.status = "IN_PROGRESS"
    o.timeline = [*o.timeline, {"status": "IN_PROGRESS", "note": "Technician started"}]
    audit(db, user.id, "ORDER_START", "order", o.id, request.client.host)
    await db.commit()
    return {"id": str(o.id), "status": o.status}


@router.post("/orders/{order_id}/complete")
async def complete_order(order_id: str, body: dict, request: Request, db: AsyncSession = Depends(get_db), user=Depends(tech)):
    import uuid
    try:
        oid = uuid.UUID(order_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Order not found")
    o = (await db.execute(select(Order).where(Order.id == oid, Order.technician_id == user.id))).scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Order not found or not assigned to you")
    o.status = "COMPLETED"
    o.completion_report = {"report": str(body.get("report", ""))[:4000], "by": str(user.id)}
    o.timeline = [*o.timeline, {"status": "COMPLETED", "note": "Technician completed"}]
    audit(db, user.id, "ORDER_COMPLETE", "order", o.id, request.client.host)
    await db.commit()
    return {"id": str(o.id), "status": o.status}
