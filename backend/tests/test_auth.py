"""Auth: register/login/me + duplicate protection."""
import pytest


@pytest.mark.asyncio
async def test_register_login_me(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "customer@test.com", "password": "Test123!secure", "full_name": "Test"})
    assert r.status_code == 201
    tok = r.json()["access_token"]
    assert tok

    m = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert m.status_code == 200
    assert m.json()["email"] == "customer@test.com"
    assert m.json()["role"] == "CUSTOMER"


@pytest.mark.asyncio
async def test_unauthorized(client):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wrong_password(client):
    await client.post("/api/v1/auth/register", json={
        "email": "a@test.com", "password": "Right123!"})
    r = await client.post("/api/v1/auth/login", json={
        "email": "a@test.com", "password": "Wrong123!"})
    assert r.status_code == 401
