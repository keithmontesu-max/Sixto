"""Orders lifecycle — customer sees only their own orders."""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Order, OrderStatus, Service, Device
from app.deps import get_current_user

router = APIRouter()


class OrderIn(BaseModel):
    service_id: str
    device_id: str
    idempotency_key: str = ""


@router.post("", status_code=201)
async def create_order(payload: OrderIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    key = payload.idempotency_key or str(uuid.uuid4())
    existing = await db.execute(select(Order).where(Order.idempotency_key == key))
    if existing.scalar_one_or_none():
        return {"message": "Order already created (idempotent)", "status": "AWAITING_PAYMENT"}
    try:
        svc_id = uuid.UUID(payload.service_id)
        dev_id = uuid.UUID(payload.device_id)
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid service or device id")
    service = await db.execute(select(Service).where(Service.id == svc_id))
    svc = service.scalar_one_or_none()
    if not svc or not svc.is_active:
        raise HTTPException(400, "Service not available")
    device = await db.execute(select(Device).where(Device.id == dev_id, Device.user_id == user.id))
    if not device.scalar_one_or_none():
        raise HTTPException(400, "Device not registered to your account")
    order = Order(user_id=user.id, device_id=dev_id, service_id=svc_id,
                  status=OrderStatus.AWAITING_PAYMENT.value, total_cents=svc.price_cents,
                  currency=svc.currency, idempotency_key=key,
                  timeline=[{"status": "PENDING", "note": "Order created"}])
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return {"id": str(order.id), "status": order.status, "total_cents": order.total_cents}


@router.get("/mine")
async def my_orders(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Order).where(Order.user_id == user.id).order_by(Order.created_at.desc()))
    return [{"id": str(o.id), "status": o.status, "total_cents": o.total_cents,
             "currency": o.currency, "created_at": str(o.created_at)} for o in result.scalars()]


@router.get("/{order_id}")
async def order_detail(order_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        oid = uuid.UUID(order_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Order not found")
    result = await db.execute(select(Order).where(Order.id == oid, Order.user_id == user.id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    return {"id": str(order.id), "status": order.status, "total_cents": order.total_cents,
            "timeline": order.timeline, "completion_report": order.completion_report}
