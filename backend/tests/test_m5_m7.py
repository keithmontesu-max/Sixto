"""M5-M7: notifications, assistant guardrails, automation, admin-ext RBAC."""
import pytest


@pytest.mark.asyncio
async def test_notifications_isolated(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "notif@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/notifications/mine", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200
    assert isinstance(r2.json(), list)


@pytest.mark.asyncio
async def test_assistant_never_invents_unapproved(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "asis@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.post("/api/v1/assistant/ask",
                           json={"question": "Can you root my Xiaomi Mi 10", "manufacturer": "Xiaomi", "model": "Mi 10"},
                           headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200
    assert "No approved" in r2.json()["answer"]
    # FAQ works
    r3 = await client.post("/api/v1/assistant/ask", json={"question": "will my data be erased"},
                           headers={"Authorization": f"Bearer {tok}"})
    assert "Back up" in r3.json()["answer"]


@pytest.mark.asyncio
async def test_automation_admin_only(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "auto@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/automation/rules", headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_remote_sessions_scoped(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "rem@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}
    s = await client.post("/api/v1/sessions", json={}, headers=headers)
    assert s.status_code == 201
    assert len(s.json()["code"]) == 8
    mine = await client.get("/api/v1/remote/sessions/mine", headers=headers)
    assert mine.status_code == 200
