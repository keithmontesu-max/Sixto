"""Final coverage: finance export, refund path, health ready."""
import pytest


@pytest.mark.asyncio
async def test_health_ready(client):
    r = await client.get("/api/v1/health/ready")
    assert r.status_code == 200
    assert r.json()["ready"] is True


@pytest.mark.asyncio
async def test_refund_and_export_require_admin(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "ref@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    r2 = await client.post("/api/v1/payments/admin/00000000-0000-0000-0000-000000000000/refund", headers=h)
    assert r2.status_code == 403
    r3 = await client.get("/api/v1/admin/finance/export", headers=h)
    assert r3.status_code == 403
