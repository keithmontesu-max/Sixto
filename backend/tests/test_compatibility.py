"""Compatibility: separate root vs bootloader, Vivo exclusion, RBAC."""
import pytest
from app.routers.compatibility import classify_record
from app.models import CompatibilityRecord


def test_separate_eligibility():
    rec = CompatibilityRecord(
        manufacturer="Xiaomi", model="Mi 10", model_id="umi",
        root_classification="ROOTABLE", bootloader_classification="BOOTLOADER_LOCKED",
        root_eligible=True, unlock_eligible=False, is_approved=True,
        supported_method="Magisk", prerequisites=["unlocked bootloader"], release_version="1.0.0")
    v = classify_record(rec)
    assert v["root"]["eligible"] is True
    assert v["bootloader"]["eligible"] is False
    assert v["supported_method"] == "Magisk"


def test_vivo_excluded_is_policy_not_technical():
    rec = CompatibilityRecord(
        manufacturer="vivo", model="Y33s", root_classification="NOT_ROOTABLE",
        is_approved=True, is_excluded=True, exclusion_reason="business policy")
    v = classify_record(rec)
    assert v["root"]["classification"] == "EXCLUDED"
    assert v["root"]["eligible"] is False


def test_unapproved_returns_unknown():
    rec = CompatibilityRecord(manufacturer="Samsung", model="S22",
                              root_classification="ROOTABLE", root_eligible=True, is_approved=False)
    v = classify_record(rec)
    assert v["root"]["classification"] == "UNKNOWN"
    assert v["root"]["eligible"] is False


@pytest.mark.asyncio
async def test_compat_rbac(client):
    # Customer cannot access admin list
    r = await client.post("/api/v1/auth/register", json={
        "email": "cust@test.com", "password": "Test123!secure"})
    tok = r.json()["access_token"]
    r2 = await client.get("/api/v1/compatibility/admin/list",
                          headers={"Authorization": f"Bearer {tok}"})
    assert r2.status_code == 403
