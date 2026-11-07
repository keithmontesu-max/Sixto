"""Device Intelligence: classification, manufacturer policy, admin CRUD."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import CompatibilityRecord, Classification
from app.deps import get_current_user, require_roles, audit

router = APIRouter()

# Business policy: EXCLUDED from initial Auto Root catalog (product restriction,
# NOT a claim that every Vivo model is technically unrootable).
MANUFACTURER_EXCLUSIONS_AUTO_ROOT = {"vivo": "EXCLUDED from initial Auto Root catalog (business policy)"}


def classify_record(rec: CompatibilityRecord) -> dict:
    """Separate root vs bootloader eligibility — never merge into one status."""
    mfr = (rec.manufacturer or "").lower()
    if rec.is_excluded or mfr in MANUFACTURER_EXCLUSIONS_AUTO_ROOT:
        return {
            "root": {"classification": Classification.EXCLUDED.value,
                     "eligible": False,
                     "reason": rec.exclusion_reason or MANUFACTURER_EXCLUSIONS_AUTO_ROOT.get(mfr, "")},
            "bootloader": {"classification": rec.bootloader_classification,
                           "eligible": rec.unlock_eligible},
            "supported_method": None,
        }
    if not rec.is_approved:
        return {
            "root": {"classification": Classification.UNKNOWN.value, "eligible": False,
                     "reason": "Not yet approved by admin"},
            "bootloader": {"classification": Classification.UNKNOWN.value, "eligible": False},
            "supported_method": None,
        }
    return {
        "root": {"classification": rec.root_classification, "eligible": rec.root_eligible},
        "bootloader": {"classification": rec.bootloader_classification, "eligible": rec.unlock_eligible},
        "supported_method": rec.supported_method if rec.root_eligible else None,
        "prerequisites": rec.prerequisites,
        "known_limitations": rec.known_limitations,
        "last_tested_date": rec.last_tested_date,
        "release_version": rec.release_version,
    }


@router.get("/lookup")
async def lookup(manufacturer: str, model: str, model_id: str = "", firmware_line: str = "",
                 db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    q = select(CompatibilityRecord).where(
        CompatibilityRecord.manufacturer.ilike(manufacturer),
        CompatibilityRecord.model.ilike(model),
        CompatibilityRecord.is_approved == True,
    )
    if model_id:
        q = q.where(CompatibilityRecord.model_id.ilike(model_id))
    else:
        q = q.where(CompatibilityRecord.model_id == "")
    result = await db.execute(q)
    rec = result.scalar_one_or_none()
    if not rec:
        return {"found": False,
                "classification": {"root": Classification.UNKNOWN.value, "bootloader": Classification.UNKNOWN.value},
                "message": "No approved compatibility record for this exact model. Diagnostics available."}
    verdict = classify_record(rec)
    return {"found": True, "manufacturer": rec.manufacturer, "model": rec.model, **verdict}


@router.get("/select-manager")
async def select_manager(manufacturer: str, model: str, model_id: str = "",
                         kernel_version: str = "", bootloader_status: str = "UNKNOWN",
                         existing_root: str = "", firmware_line: str = "",
                         db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Intelligent selection — returns recommended manager or explains why none.
    Requires an approved compatibility record. Never guesses."""
    from app.services.root_manager import DeviceSignals, select_root_manager
    q = select(CompatibilityRecord).where(
        CompatibilityRecord.manufacturer.ilike(manufacturer),
        CompatibilityRecord.model.ilike(model),
        CompatibilityRecord.is_approved == True,
    )
    if model_id:
        q = q.where(CompatibilityRecord.model_id.ilike(model_id))
    else:
        q = q.where(CompatibilityRecord.model_id == "")
    result = await db.execute(q)
    rec = result.scalar_one_or_none()
    if not rec:
        return {"recommended": None, "reason": "No approved compatibility record. Diagnostics only.",
                "prerequisites": [], "warnings": [], "requires_authorization": True,
                "classification": {"root": "UNKNOWN", "bootloader": "UNKNOWN"}}
    verdict = classify_record(rec)
    signals = DeviceSignals(manufacturer=rec.manufacturer, model=rec.model,
                            kernel_version=kernel_version, bootloader_status=bootloader_status,
                            existing_root=existing_root, firmware_line=firmware_line)
    sel = select_root_manager(signals, verdict)
    return {"recommended": sel.recommended, "reason": sel.reason, "prerequisites": sel.prerequisites,
            "warnings": sel.warnings, "requires_authorization": sel.requires_authorization,
            "classification": {"root": verdict["root"], "bootloader": verdict["bootloader"]},
            "supported_method": verdict.get("supported_method")}


# --- Admin only ---

class CompatIn(BaseModel):
    manufacturer: str
    model: str
    model_id: str = ""
    hardware_variant: str = ""
    chipset: str = ""
    architecture: str = ""
    android_version: str = ""
    firmware_line: str = ""
    root_classification: str = "UNKNOWN"
    bootloader_classification: str = "UNKNOWN"
    root_eligible: bool = False
    unlock_eligible: bool = False
    supported_method: str = ""
    prerequisites: list = []
    known_limitations: list = []
    is_approved: bool = False
    is_excluded: bool = False
    exclusion_reason: str = ""
    last_tested_date: str = ""
    release_version: str = "1.0.0"


@router.get("/admin/list")
async def admin_list(db: AsyncSession = Depends(get_db),
                     user=Depends(require_roles("OWNER", "SUPER_ADMIN", "ADMIN"))):
    result = await db.execute(select(CompatibilityRecord).limit(200))
    return [{"id": str(r.id), "manufacturer": r.manufacturer, "model": r.model,
             "root_classification": r.root_classification, "root_eligible": r.root_eligible,
             "is_approved": r.is_approved, "is_excluded": r.is_excluded} for r in result.scalars()]


@router.post("/admin/upsert")
async def admin_upsert(payload: CompatIn, request: Request, db: AsyncSession = Depends(get_db),
                       user=Depends(require_roles("OWNER", "SUPER_ADMIN", "ADMIN"))):
    q = select(CompatibilityRecord).where(
        CompatibilityRecord.manufacturer.ilike(payload.manufacturer),
        CompatibilityRecord.model.ilike(payload.model),
        CompatibilityRecord.hardware_variant == payload.hardware_variant,
        CompatibilityRecord.firmware_line == payload.firmware_line,
    )
    rec = (await db.execute(q)).scalar_one_or_none()
    data = payload.model_dump()
    if rec:
        for k, v in data.items():
            setattr(rec, k, v)
    else:
        rec = CompatibilityRecord(**data)
        db.add(rec)
    audit(db, user.id, "COMPAT_UPSERT", "compatibility", rec.model, request.client.host, {"approved": payload.is_approved})
    await db.commit()
    await db.refresh(rec)
    return {"id": str(rec.id)}
