"""Business: service admin RBAC, coupon math, webhook signature (fail closed)."""
import hashlib
import hmac
import pytest
import pytest_asyncio
from app.routers.coupons import apply_coupon
from app.models import Coupon


def test_coupon_percent_math():
    c = Coupon(code="SAVE10", discount_percent=10, discount_cents=0, is_active=True)
    r = apply_coupon(c, 100_000)
    assert r["discount_cents"] == 10_000
    assert r["final_cents"] == 90_000


def test_coupon_fixed_wins_and_clamps():
    c = Coupon(code="MINUS", discount_percent=50, discount_cents=500_000, is_active=True)
    r = apply_coupon(c, 100_000)
    assert r["discount_cents"] == 100_000
    assert r["final_cents"] == 0


def test_coupon_rejects_inactive_and_limit():
    c = Coupon(code="X", is_active=False)
    with pytest.raises(Exception):
        apply_coupon(c, 1000)
    c2 = Coupon(code="X", is_active=True, max_uses=1, used_count=1)
    with pytest.raises(Exception):
        apply_coupon(c2, 1000)


@pytest.mark.asyncio
async def test_service_admin_rbac(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "svc@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}
    # Customer cannot list admin services
    r2 = await client.get("/api/v1/services/admin/all", headers=headers)
    assert r2.status_code == 403
    # Customer can see catalog endpoint (empty list is fine)
    r3 = await client.get("/api/v1/services", headers=headers)
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_webhook_fails_closed_without_secret(client, monkeypatch):
    # No PAY_WEBHOOK_SECRET_GCASH set → webhook must 401, never auto-pay.
    monkeypatch.delenv("PAY_WEBHOOK_SECRET_GCASH", raising=False)
    r = await client.post("/api/v1/payments/webhook/GCASH", json={
        "provider_ref": "nope", "status": "PAID"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_webhook_signature_verification(client, monkeypatch):
    monkeypatch.setenv("PAY_WEBHOOK_SECRET_GCASH", "test-secret-123")
    body = b'{"provider_ref":"unknown-1","status":"PAID"}'
    sig = hmac.new(b"test-secret-123", body, hashlib.sha256).hexdigest()
    r = await client.post("/api/v1/payments/webhook/GCASH", content=body,
                          headers={"Content-Type": "application/json", "x-signature": sig})
    assert r.status_code == 200  # unknown ref → 200 (no leak) but verified
    # Bad signature → 401
    r2 = await client.post("/api/v1/payments/webhook/GCASH", content=body,
                           headers={"Content-Type": "application/json", "x-signature": "bad"})
    assert r2.status_code == 401
