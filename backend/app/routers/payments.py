"""Payments: server-side verification only. Never trust screenshots.

Direct-payment model: customer pays the OWNER directly (GCash/Maya number
configured in BusinessConfig), then submits reference in-app. OWNER verifies
in his own wallet app and confirms in admin. App never holds money; it only
tracks the paper trail. Webhook path is kept for future gateway upgrades.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Payment, Order, OrderStatus, Coupon, BusinessConfig
from app.deps import get_current_user, require_roles, audit
from app.providers.verify import require_verified, extract_provider_ref

router = APIRouter()

PROVIDERS = {"GCASH", "MAYA", "CARD", "MANUAL"}
admin_only = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")


async def _payment_methods(db: AsyncSession) -> dict:
    cfg = (await db.execute(select(BusinessConfig).where(BusinessConfig.key == "payment_methods"))).scalar_one_or_none()
    if cfg:
        return cfg.value or {}
    return {"gcash_number": "", "gcash_name": "", "maya_number": "", "maya_name": "",
            "instructions": "Pay the owner directly, then submit your reference for verification."}


@router.get("/methods")
async def methods(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Show owner-direct payment details (numbers come from backend, never hardcoded)."""
    m = await _payment_methods(db)
    return {"methods": m,
            "note": "Pay the owner directly. Submit your reference here. The owner verifies in his wallet app."}


class PaymentIn(BaseModel):
    order_id: str
    provider: str = "MANUAL"  # GCASH|MAYA|CARD|MANUAL — MANUAL = direct to owner
    provider_ref: str
    coupon_code: str = ""


@router.post("/initiate", status_code=201)
async def initiate_payment(payload: PaymentIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    if payload.provider.upper() not in PROVIDERS:
        raise HTTPException(400, "Unsupported provider")
    if not (payload.provider_ref or "").strip():
        raise HTTPException(400, "Transaction reference is required")
    try:
        oid = uuid.UUID(payload.order_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Order not found")
    order = await db.execute(select(Order).where(Order.id == oid, Order.user_id == user.id))
    o = order.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Order not found")
    dup = await db.execute(select(Payment).where(Payment.provider_ref == payload.provider_ref))
    if dup.scalar_one_or_none():
        raise HTTPException(409, "Duplicate transaction reference")

    amount = o.total_cents
    if payload.coupon_code:
        c = (await db.execute(select(Coupon).where(Coupon.code.ilike(payload.coupon_code)))).scalar_one_or_none()
        if c:
            from app.routers.coupons import apply_coupon
            result = apply_coupon(c, o.total_cents)  # raises 400 if invalid
            amount = result["final_cents"]
            c.used_count += 1
    else:
        c = None

    payment = Payment(order_id=oid, provider=payload.provider.upper(),
                      provider_ref=payload.provider_ref, amount_cents=amount,
                      currency=o.currency, status="PENDING")
    db.add(payment)
    o.status = OrderStatus.AWAITING_PAYMENT.value
    await db.commit()
    return {"id": str(payment.id), "status": "PENDING", "amount_cents": amount,
            "message": "Awaiting provider verification (webhook with signature)"}


@router.post("/webhook/{provider}")
async def webhook(provider: str, request: Request, db: AsyncSession = Depends(get_db)):
    """Provider webhooks — signature verified with HMAC-SHA256 over raw body.

    Fail closed: no secret configured → 401. Invalid signature → 401.
    Unknown provider_ref → still 200 (do not leak existence) but logged.
    """
    provider_norm = provider.upper()
    if provider_norm not in PROVIDERS:
        raise HTTPException(400, "Unsupported provider")
    raw = await request.body()
    signature = request.headers.get("x-signature") or request.headers.get("X-Signature") or ""
    require_verified(provider_norm, raw, signature)

    try:
        body_raw = await request.json()
    except Exception:
        try:
            import json
            body_raw = json.loads(raw.decode() or "{}")
        except Exception:
            raise HTTPException(400, "Invalid JSON body")
    provider_ref = extract_provider_ref(body_raw)
    status = (body_raw.get("status") or body_raw.get("state") or "").upper()
    result = await db.execute(select(Payment).where(Payment.provider_ref == provider_ref))
    payment = result.scalar_one_or_none()
    if not payment:
        audit(db, None, "PAYMENT_WEBHOOK_UNKNOWN_REF", "payment", "", request.client.host, {"provider": provider_norm})
        await db.commit()
        return {"ok": True}
    payment.raw_webhook = body_raw
    payment.webhook_verified = True
    if status in ("PAID", "SUCCESS", "COMPLETED", "CAPTURED"):
        payment.status = "PAID"
        order = await db.execute(select(Order).where(Order.id == payment.order_id))
        o = order.scalar_one_or_none()
        if o:
            o.status = OrderStatus.PAYMENT_CONFIRMED.value
            o.timeline = [*o.timeline, {"status": "PAYMENT_CONFIRMED", "note": f"{provider_norm} verified"}]
    elif status in ("FAILED", "DECLINED", "CANCELLED"):
        payment.status = "FAILED"
    audit(db, None, "PAYMENT_WEBHOOK", "payment", payment.id, request.client.host, {"provider": provider_norm, "status": status})
    await db.commit()
    return {"ok": True}


@router.post("/admin/{payment_id}/confirm")
async def admin_confirm(payment_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    """OWNER verifies the direct transfer in his own wallet app, then confirms here."""
    try:
        pid = uuid.UUID(payment_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Payment not found")
    p = (await db.execute(select(Payment).where(Payment.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Payment not found")
    if p.status == "PAID":
        return {"id": str(p.id), "status": "PAID"}
    p.status = "PAID"
    p.webhook_verified = True
    p.raw_webhook = {"manual_confirm_by": str(user.id), "via": "direct_wallet_check"}
    o = (await db.execute(select(Order).where(Order.id == p.order_id))).scalar_one_or_none()
    if o:
        o.status = OrderStatus.PAYMENT_CONFIRMED.value
        o.timeline = [*o.timeline, {"status": "PAYMENT_CONFIRMED", "note": "Owner verified direct payment"}]
        # Template notification (respects ntf_payment pref via client check; stored either way).
        from app.models import Notification, BusinessConfig, User
        cfg = (await db.execute(select(BusinessConfig).where(BusinessConfig.key == "notif_templates"))).scalar_one_or_none()
        tpl = (cfg.value if cfg else {}).get("payment_confirmed", {"title": "Payment received", "body": "Payment confirmed for order {order_id}."})
        try:
            title = str(tpl.get("title", "")).format(order_id=str(o.id)[:8])
            body = str(tpl.get("body", "")).format(order_id=str(o.id)[:8])
        except Exception:
            title, body = "Payment received", f"Payment confirmed for order {str(o.id)[:8]}."
        db.add(Notification(user_id=o.user_id, title=title, body=body, kind="payment"))
        # Best-effort mirrors (log-only unless env configured; never fail the confirm).
        try:
            from app.services.notify_adapters import EmailAdapter, PushAdapter
            owner = (await db.execute(select(User).where(User.id == o.user_id))).scalar_one_or_none()
            if owner:
                EmailAdapter().send(owner.email, title, body)
                # Push: need token rows
                from app.models import PushToken
                toks = (await db.execute(select(PushToken).where(PushToken.user_id == o.user_id))).scalars().all()
                for t in toks:
                    PushAdapter().send(t.token, title, body)
        except Exception:
            pass
    audit(db, user.id, "PAYMENT_CONFIRM", "payment", p.id, request.client.host, {"order": str(p.order_id)})
    await db.commit()
    return {"id": str(p.id), "status": "PAID"}


@router.post("/admin/{payment_id}/reject")
async def admin_reject(payment_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    try:
        pid = uuid.UUID(payment_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Payment not found")
    p = (await db.execute(select(Payment).where(Payment.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Payment not found")
    p.status = "FAILED"
    audit(db, user.id, "PAYMENT_REJECT", "payment", p.id, request.client.host)
    await db.commit()
    return {"id": str(p.id), "status": "FAILED"}


@router.post("/admin/{payment_id}/refund")
async def admin_refund(payment_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(admin_only)):
    """Owner refunds manually in his wallet, then marks REFUNDED here. Order → REFUNDED."""
    try:
        pid = uuid.UUID(payment_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Payment not found")
    p = (await db.execute(select(Payment).where(Payment.id == pid))).scalar_one_or_none()
    if not p:
        raise HTTPException(404, "Payment not found")
    p.status = "REFUNDED"
    o = (await db.execute(select(Order).where(Order.id == p.order_id))).scalar_one_or_none()
    if o:
        o.status = OrderStatus.REFUNDED.value
        o.timeline = [*o.timeline, {"status": "REFUNDED", "note": "Owner refunded directly"}]
    audit(db, user.id, "PAYMENT_REFUND", "payment", p.id, request.client.host)
    await db.commit()
    return {"id": str(p.id), "status": "REFUNDED"}


@router.get("/history")
async def my_payments(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    q = select(Payment).join(Order, Order.id == Payment.order_id).where(Order.user_id == user.id)
    result = await db.execute(q)
    return [{"id": str(p.id), "provider": p.provider, "provider_ref": p.provider_ref,
             "amount_cents": p.amount_cents, "status": p.status} for p in result.scalars()]
