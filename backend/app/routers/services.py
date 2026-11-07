"""Service catalog — backend-driven only. No hardcoded prices in client.

Customer: GET /services (active only, device-gated by caller via compatibility).
Admin:  GET/POST /services/admin/* for create/edit/disable/publish (OWNER/SUPER_ADMIN/ADMIN).
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Service
from app.deps import get_current_user, require_roles, audit

router = APIRouter()
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")


@router.get("")
async def catalog(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Service).where(Service.is_active == True))
    services = result.scalars()
    return [{"id": str(s.id), "name": s.name, "slug": s.slug, "description": s.description,
             "category": s.category, "price_cents": s.price_cents, "currency": s.currency,
             "eta_minutes": s.eta_minutes, "requires_root_eligible": s.requires_root_eligible,
             "refund_policy": s.refund_policy} for s in services]


# --- Admin CRUD (pricing lives here, never in the APK) ---

class ServiceIn(BaseModel):
    name: str
    slug: str
    description: str = ""
    category: str = "ROOT"
    price_cents: int = 0
    currency: str = "PHP"
    eta_minutes: int = 0
    is_active: bool = True
    requires_root_eligible: bool = True
    refund_policy: str = ""
    terms: str = ""


@router.get("/admin/all")
async def admin_all(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(Service))
    return [{"id": str(s.id), "name": s.name, "slug": s.slug, "price_cents": s.price_cents,
             "is_active": s.is_active, "category": s.category} for s in result.scalars()]


@router.post("/admin/upsert")
async def admin_upsert(payload: ServiceIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    if payload.price_cents < 0:
        raise HTTPException(400, "Price cannot be negative")
    existing = await db.execute(select(Service).where(Service.slug == payload.slug))
    svc = existing.scalar_one_or_none()
    if svc:
        for k, v in payload.model_dump().items():
            setattr(svc, k, v)
    else:
        svc = Service(**payload.model_dump())
        db.add(svc)
        await db.flush()
    audit(db, user.id, "SERVICE_UPSERT", "service", svc.id, request.client.host, {"active": payload.is_active, "price": payload.price_cents})
    await db.commit()
    await db.refresh(svc)
    return {"id": str(svc.id), "slug": svc.slug}


@router.post("/admin/{service_id}/toggle")
async def admin_toggle(service_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    try:
        sid = uuid.UUID(service_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Service not found")
    svc = (await db.execute(select(Service).where(Service.id == sid))).scalar_one_or_none()
    if not svc:
        raise HTTPException(404, "Service not found")
    svc.is_active = not svc.is_active
    audit(db, user.id, "SERVICE_TOGGLE", "service", svc.id, request.client.host, {"active": svc.is_active})
    await db.commit()
    return {"id": str(svc.id), "is_active": svc.is_active}
