"""Notification templates — admin-configurable, stored as BusinessConfig `notif_templates`.

Seed defaults used when no config exists. Templates use {order_id} / {amount} placeholders.
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import BusinessConfig
from app.deps import get_current_user, require_roles, audit

router = APIRouter()
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")

DEFAULTS = {
    "order_confirmation": {"title": "Order confirmed", "body": "Order {order_id} confirmed. Pay {amount} then submit your reference."},
    "payment_confirmed": {"title": "Payment received", "body": "Payment confirmed for order {order_id}."},
    "technician_assigned": {"title": "Technician assigned", "body": "A technician was assigned to order {order_id}."},
    "service_completed": {"title": "Service completed", "body": "Order {order_id} completed. Report is in My Orders."},
    "session_invite": {"title": "Support session", "body": "Your session code is {code}. Share it with your technician."},
}


def render(template: dict, ctx: dict) -> dict:
    return {
        "title": str(template.get("title", "")).format(**ctx),
        "body": str(template.get("body", "")).format(**ctx),
    }


@router.get("")
async def get_templates(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    cfg = (await db.execute(select(BusinessConfig).where(BusinessConfig.key == "notif_templates"))).scalar_one_or_none()
    return {"templates": cfg.value if cfg else DEFAULTS, "is_default": cfg is None}


class TemplatesIn(BaseModel):
    templates: dict


@router.post("")
async def set_templates(payload: TemplatesIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    cfg = (await db.execute(select(BusinessConfig).where(BusinessConfig.key == "notif_templates"))).scalar_one_or_none()
    if cfg:
        cfg.value = payload.templates
    else:
        cfg = BusinessConfig(key="notif_templates", value=payload.templates)
        db.add(cfg)
    audit(db, user.id, "TEMPLATES_UPDATE", "business_config", "notif_templates", request.client.host)
    await db.commit()
    return {"ok": True}
