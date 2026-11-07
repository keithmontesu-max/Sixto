"""Root manager selection: must never guess, must block unsupported devices."""
import pytest
from app.services.root_manager import DeviceSignals, select_root_manager


def test_no_method_when_not_eligible():
    compat = {"root": {"classification": "NOT_ROOTABLE", "eligible": False}, "supported_method": None}
    sel = select_root_manager(DeviceSignals(manufacturer="Xiaomi", model="Mi 10"), compat)
    assert sel.recommended is None
    assert sel.requires_authorization is True


def test_magisk_selection_when_approved():
    compat = {"root": {"classification": "ROOTABLE", "eligible": True},
              "supported_method": "Magisk", "prerequisites": ["test 1"]}
    sel = select_root_manager(DeviceSignals(), compat)
    assert sel.recommended == "Magisk"


def test_existing_root_migration_blocked():
    compat = {"root": {"classification": "ROOTABLE", "eligible": True},
              "supported_method": "KernelSU", "prerequisites": []}
    sel = select_root_manager(DeviceSignals(existing_root="Magisk"), compat)
    assert sel.recommended is None
    assert "migration" in sel.reason.lower() or "authorization" in sel.reason.lower()


def test_never_guesses_when_method_missing():
    compat = {"root": {"classification": "ROOTABLE", "eligible": True},
              "supported_method": None, "prerequisites": []}
    sel = select_root_manager(DeviceSignals(), compat)
    assert sel.recommended is None


@pytest.mark.asyncio
async def test_select_manager_api_rejects_unapproved(client):
    r = await client.post("/api/v1/auth/register", json={
        "email": "mgr@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/compatibility/select-manager", params={
        "manufacturer": "Xiaomi", "model": "Mi 10"},
        headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 200
    assert r2.json()["recommended"] is None
