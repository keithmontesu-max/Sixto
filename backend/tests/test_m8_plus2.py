"""M8+: security headers + admin orders + technician complete flow."""
import pytest


@pytest.mark.asyncio
async def test_security_headers_present(client):
    r = await client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.headers.get("x-content-type-options") == "nosniff"
    assert r.headers.get("x-frame-options") == "DENY"


@pytest.mark.asyncio
async def test_admin_orders_requires_admin(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "admord@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/admin/orders", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_technician_complete_scoped(client):
    # Customer cannot complete others' orders (403 via tech guard).
    r = await client.post("/api/v1/auth/register", json={
        "email": "techflow@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.post("/api/v1/technician/orders/00000000-0000-0000-0000-000000000000/start",
                           headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 403
