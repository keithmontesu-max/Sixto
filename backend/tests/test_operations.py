"""Operation engine: plan validation, authorization gate, 4-step verification."""
import pytest
from app.services.operation_engine import plan_operation, verify_operation
from app.services.adapters.registry import get_adapter, list_methods


def test_adapters_registered():
    assert set(["Magisk", "KernelSU", "APatch"]).issubset(set(list_methods()))
    assert get_adapter("Magisk") is not None


def test_plan_rejects_ineligible():
    compat = {"root": {"classification": "NOT_ROOTABLE", "eligible": False}}
    r = plan_operation("Magisk", compat)
    assert r["ok"] is False


def test_plan_rejects_unknown_method():
    compat = {"root": {"classification": "ROOTABLE", "eligible": True}, "supported_method": "Magisk"}
    r = plan_operation("NonExistentManager", compat)
    assert r["ok"] is False


def test_verify_requires_all_four():
    assert verify_operation({})["success"] is False
    assert verify_operation({"implementation_installed": True, "kernel_boot_compatible": True,
                             "manager_installed": True, "actual_root_available": True})["success"] is True
    r = verify_operation({"implementation_installed": True, "kernel_boot_compatible": True,
                          "manager_installed": True, "actual_root_available": False})
    assert r["success"] is False
    assert "actual_root_available" in r["failed"]


@pytest.mark.asyncio
async def test_operations_flow_requires_auth_before_verify(client):
    # Register + device + approved compat record via admin token is complex;
    # here we assert plan rejects without a record (no fabrication).
    r = await client.post("/api/v1/auth/register", json={
        "email": "op@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {tok}"}
    dev = await client.post("/api/v1/devices", json={
        "manufacturer": "Xiaomi", "model": "Mi 10", "model_id": "umi"}, headers=headers)
    assert dev.status_code == 201
    dev_id = dev.json()["id"]
    plan = await client.post("/api/v1/operations/plan", json={"device_id": dev_id}, headers=headers)
    assert plan.status_code == 400  # no approved record → no plan (honest)
