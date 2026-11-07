"""Root method registry (System D backing). OWNER-only approval; ADMIN can view.

Each record: method id, supported devices/firmware, prerequisites, version,
validation status, security review, known issues, last tested, deprecation.

Disabling a method immediately blocks new Auto Root offerings that rely on it
(compatibility lookup returns UNKNOWN for those records).
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import CompatibilityRecord
from app.deps import require_roles, get_current_user, audit

router = APIRouter()

admin_view = require_roles("OWNER", "SUPER_ADMIN", "ADMIN")
owner_write = require_roles("OWNER", "SUPER_ADMIN")


class MethodToggleIn(BaseModel):
    method: str  # Magisk | KernelSU | APatch
    enable: bool
    review_note: str = ""


@router.get("")
async def list_methods(db: AsyncSession = Depends(get_db), user=Depends(admin_view)):
    result = await db.execute(select(CompatibilityRecord).where(CompatibilityRecord.root_eligible == True))
    by_method: dict[str, list] = {}
    for r in result.scalars():
        by_method.setdefault(r.supported_method or "UNSET", []).append({
            "id": str(r.id), "manufacturer": r.manufacturer, "model": r.model,
            "firmware_line": r.firmware_line, "last_tested_date": r.last_tested_date,
            "release_version": r.release_version, "known_limitations": r.known_limitations,
        })
    return {"methods": [{"method": m, "count": len(v), "records": v} for m, v in sorted(by_method.items())]}


@router.post("/toggle")
async def toggle_method(payload: MethodToggleIn, request: Request,
                        db: AsyncSession = Depends(get_db), user=Depends(owner_write)):
    """Enable/disable a method platform-wide by flipping root_eligible on its records.

    In production, prefer a dedicated `root_methods` table; this uses the
    compatibility table as the registry until M6 splits it. Every toggle audits.
    """
    result = await db.execute(select(CompatibilityRecord).where(CompatibilityRecord.supported_method == payload.method))
    records = result.scalars().all()
    if not records:
        return {"method": payload.method, "affected": 0, "message": "No records found"}
    for r in records:
        r.root_eligible = bool(payload.enable)
        if payload.enable:
            r.root_classification = "ROOTABLE"
        else:
            # Disabled methods must not report ROOTABLE.
            if r.root_classification == "ROOTABLE":
                r.root_classification = "UNKNOWN"
    audit(db, user.id, "ROOT_METHOD_TOGGLE", "root_method", payload.method,
          request.client.host, {"enable": payload.enable, "note": payload.review_note})
    await db.commit()
    return {"method": payload.method, "affected": len(records), "enabled": payload.enable}
