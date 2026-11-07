"""M8+: push, templates, technician portal coverage."""
import pytest


@pytest.mark.asyncio
async def test_push_token_register_and_list(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "push@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    p = await client.post("/api/v1/push/register", json={"token": "fcm-token-123", "platform": "android"}, headers=h)
    assert p.status_code == 200
    lst = await client.get("/api/v1/push/mine", headers=h)
    assert lst.status_code == 200
    assert any(t["token"] == "fcm-token-123" for t in lst.json())


@pytest.mark.asyncio
async def test_templates_defaults(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "tpl@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/templates", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200
    assert "payment_confirmed" in r2.json()["templates"]


@pytest.mark.asyncio
async def test_technician_portal_scoped(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "techp@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    # Customer cannot hit technician portal.
    r2 = await client.get("/api/v1/technician/my-orders", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_tech_requires_owner(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "notowner@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/tech/status", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 403
