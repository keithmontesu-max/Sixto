"""OWNER-ONLY photo/screenshot analysis (TECHTOOL).

Upload a screenshot of Settings → About phone (model, build, kernel).
We extract text via OCR when available and match to compatibility.

Honest limits:
- Physical photo of a phone screen is unreliable (glare, angle, small font).
- Kernel version is small text — screenshot is required for auto-read.
- If OCR fails, we return manual-entry fields — never guess.

Security: file-type + size validated, stored isolated, never executed.
"""
import io
import re
import uuid
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.deps import require_roles
from app.models import CompatibilityRecord
from app.routers.compatibility import classify_record

router = APIRouter()
owner_only = require_roles("OWNER")

MAX_BYTES = 8 * 1024 * 1024  # 8 MB
ALLOWED = {"image/jpeg", "image/png", "image/webp"}


def _extract_signals(ocr_text: str) -> dict:
    """Best-effort regex extraction from About-page OCR."""
    text = ocr_text or ""
    signals = {"manufacturer": "", "model": "", "model_id": "", "android_version": "", "kernel_version": "", "build_fingerprint": "", "raw": text[:4000]}
    # Build fingerprint: brand/product/device:version/id/...
    fp = re.search(r"[A-Za-z0-9._\-]+/[A-Za-z0-9._\-]+/[A-Za-z0-9._\-]+:[A-Za-z0-9._\-]+/[A-Za-z0-9._\-]+/[A-Za-z0-9._\-]+", text)
    if fp:
        signals["build_fingerprint"] = fp.group(0)
        parts = fp.group(0).split("/")
        if parts:
            signals["manufacturer"] = parts[0].split("-")[0]
    # Android version line
    m = re.search(r"Android\s+(1[0-6]|[0-9])", text, re.I)
    if m:
        signals["android_version"] = m.group(1)
    # Kernel: Linux version 5.x
    k = re.search(r"Linux version\s+([0-9]+\.[0-9]+\.[0-9]+)", text, re.I)
    if k:
        signals["kernel_version"] = k.group(1)
    # Model line (best effort: after "Model" label)
    mod = re.search(r"Model\s*[:\-]?\s*([A-Za-z0-9 \-\_]{2,40})", text, re.I)
    if mod:
        signals["model"] = mod.group(1).strip()
    return signals


@router.post("/analyze-photo")
async def analyze_photo(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user=Depends(owner_only)):
    if file.content_type not in ALLOWED:
        raise HTTPException(400, "Only JPG/PNG/WEBP screenshots allowed")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(400, "File too large (max 8 MB)")
    # Minimal magic-byte check (JPEG/PNG)
    if not (data.startswith(b"\xff\xd8") or data.startswith(b"\x89PNG") or data.startswith(b"RIFF")):
        raise HTTPException(400, "Invalid image file")

    # Isolated handling in-memory (no exec, no serving). Hash for audit.
    import hashlib
    digest = hashlib.sha256(data).hexdigest()[:16]

    ocr_text = ""
    ocr_note = "OCR not available — manual entry required"
    try:
        from PIL import Image
        import pytesseract
        img = Image.open(io.BytesIO(data))
        ocr_text = pytesseract.image_to_string(img)
        ocr_note = "OCR extracted (review before approving)"
    except Exception as e:
        ocr_note = f"OCR unavailable ({type(e).__name__}) — manual entry required"

    signals = _extract_signals(ocr_text)

    # Auto-lookup if we got manufacturer+model
    compat = None
    if signals["manufacturer"] and signals["model"]:
        q = select(CompatibilityRecord).where(
            CompatibilityRecord.manufacturer.ilike(signals["manufacturer"]),
            CompatibilityRecord.model.ilike(signals["model"]),
        )
        rec = (await db.execute(q)).scalar_one_or_none()
        compat = classify_record(rec) if rec else {
            "root": {"classification": "UNKNOWN", "eligible": False, "reason": "No record for extracted model"},
            "bootloader": {"classification": "UNKNOWN", "eligible": False},
            "supported_method": None,
        }

    return {
        "image_hash": digest,
        "ocr_note": ocr_note,
        "signals": signals,
        "compatibility": compat,
        "instruction": "Review extracted fields. Correct manufacturer/model/build manually if OCR missed. Screenshot of About phone is required for kernel auto-read — physical photos rarely work.",
    }
