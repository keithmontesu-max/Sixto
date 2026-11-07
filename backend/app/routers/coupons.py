"""Coupons — backend-only. Discounts compute server-side."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Coupon
from app.deps import get_current_user, require_roles, audit

router = APIRouter()
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")


def apply_coupon(coupon: Coupon, subtotal_cents: int) -> dict:
    """Returns {discount_cents, final_cents, code} or raises 400."""
    if not coupon.is_active:
        raise HTTPException(400, "Coupon is not active")
    if coupon.max_uses and coupon.used_count >= coupon.max_uses:
        raise HTTPException(400, "Coupon usage limit reached")
    if coupon.min_order_cents and subtotal_cents < coupon.min_order_cents:
        raise HTTPException(400, f"Requires minimum order of {coupon.min_order_cents} cents")
    if coupon.discount_cents > 0:
        discount = min(coupon.discount_cents, subtotal_cents)
    else:
        discount = int(subtotal_cents * max(0, min(coupon.discount_percent, 100)) / 100)
    return {"discount_cents": discount, "final_cents": subtotal_cents - discount, "code": coupon.code}


class ValidateIn(BaseModel):
    code: str
    subtotal_cents: int


@router.post("/validate")
async def validate(payload: ValidateIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    c = (await db.execute(select(Coupon).where(Coupon.code.ilike(payload.code)))).scalar_one_or_none()
    if not c:
        raise HTTPException(400, "Invalid coupon code")
    return apply_coupon(c, payload.subtotal_cents)


class CouponIn(BaseModel):
    code: str
    discount_percent: int = 0
    discount_cents: int = 0
    is_active: bool = True
    max_uses: int = 0
    min_order_cents: int = 0


@router.get("/admin/all")
async def admin_all(db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    result = await db.execute(select(Coupon))
    return [{"id": str(c.id), "code": c.code, "discount_percent": c.discount_percent,
             "discount_cents": c.discount_cents, "is_active": c.is_active,
             "used_count": c.used_count, "max_uses": c.max_uses} for c in result.scalars()]


@router.post("/admin/upsert")
async def admin_upsert(payload: CouponIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    if not (0 <= payload.discount_percent <= 100):
        raise HTTPException(400, "Percent must be 0–100")
    existing = await db.execute(select(Coupon).where(Coupon.code.ilike(payload.code)))
    c = existing.scalar_one_or_none()
    if c:
        for k, v in payload.model_dump().items():
            setattr(c, k, v)
    else:
        c = Coupon(**payload.model_dump())
        db.add(c)
        await db.flush()
    audit(db, user.id, "COUPON_UPSERT", "coupon", c.id, request.client.host)
    await db.commit()
    await db.refresh(c)
    return {"id": str(c.id), "code": c.code}
