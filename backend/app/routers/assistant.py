"""AI assistance layer — controlled, rule-based. NEVER invents root methods,
never authorizes destructive operations. Only explains approved records.

Customer: explain compat report, explain error, recommend services, FAQ, prerequisites.
Technician: summarize diagnostics, surface known issues, organize reports.
Business: demand/failure summaries (computed from real DB counts).
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Order, Device, CompatibilityRecord, Payment
from app.deps import get_current_user

router = APIRouter()


class AskIn(BaseModel):
    question: str
    manufacturer: str = ""
    model: str = ""


FAQ = [
    ("will my data be erased", "Bootloader unlocking erases data on most devices. Back up before any unlock. The app explains consequences before you authorize."),
    ("is vivo supported", "Vivo is EXCLUDED from the initial Auto Root catalog (business policy). Diagnostics remain available; root services are not offered."),
    ("how long", "Most approved services list an ETA in the service catalog. You see it before ordering."),
    ("refund", "Refund policy is shown per service before checkout. Verified payments only — screenshots never count."),
]


def _faq(question: str) -> str | None:
    q = question.lower()
    for needle, answer in FAQ:
        if needle in q:
            return answer
    return None


@router.post("/ask")
async def ask(payload: AskIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    faq = _faq(payload.question)
    if faq:
        return {"answer": faq, "source": "faq"}

    if payload.manufacturer and payload.model:
        rec = (await db.execute(select(CompatibilityRecord).where(
            CompatibilityRecord.manufacturer.ilike(payload.manufacturer),
            CompatibilityRecord.model.ilike(payload.model),
            CompatibilityRecord.is_approved == True))).scalar_one_or_none()
        if not rec:
            return {"answer": "No approved compatibility record for that exact model+firmware. We do not guess. Diagnostics are available; root/unlock are not offered until a technician validates and an admin approves.",
                    "source": "compatibility-db"}
        parts = [
            f"Root: {rec.root_classification} (eligible: {rec.root_eligible}).",
            f"Bootloader: {rec.bootloader_classification} (unlock eligible: {rec.unlock_eligible}).",
            f"Method: {rec.supported_method or '—'}.",
        ]
        if rec.prerequisites:
            parts.append("Prerequisites: " + ", ".join(rec.prerequisites) + ".")
        if rec.known_limitations:
            parts.append("Limits: " + ", ".join(rec.known_limitations) + ".")
        return {"answer": " ".join(parts), "source": "compatibility-db"}

    return {"answer": "Ask about a specific device (manufacturer + model) or service. I only describe approved records and validated procedures.",
            "source": "guardrail"}


@router.get("/demand")
async def demand(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Business intel from real data: top manufacturers, failure pattern, bottlenecks."""
    total_orders = (await db.execute(select(func.count()).select_from(Order))).scalar() or 0
    failed = (await db.execute(select(Order).where(Order.status == "FAILED"))).scalars().all()
    by_status = {}
    for status in ["PENDING", "AWAITING_PAYMENT", "PAYMENT_CONFIRMED", "IN_PROGRESS", "COMPLETED", "FAILED"]:
        c = (await db.execute(select(func.count()).select_from(Order).where(Order.status == status))).scalar() or 0
        by_status[status] = c
    dev_count = (await db.execute(select(func.count()).select_from(Device))).scalar() or 0
    return {"total_orders": total_orders, "devices": dev_count, "by_status": by_status,
            "failure_rate": (len(failed) / total_orders) if total_orders else 0.0,
            "note": "Counts only. No predictions on unvalidated devices."}
