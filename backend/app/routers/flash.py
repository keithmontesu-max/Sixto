"""OWNER-ONLY flash orchestration (TECHTOOL). No arbitrary shell — allowlisted fastboot/adb only."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from app.deps import require_roles, audit

router = APIRouter()
owner_only = require_roles("OWNER")


class PlanIn(BaseModel):
    patched_image: str
    do_vbmeta: bool = False


@router.post("/plan")
async def plan(payload: PlanIn, request: Request, user=Depends(owner_only)):
    from app.services.flasher import plan_flash, new_flash_id
    result = plan_flash(payload.patched_image, payload.do_vbmeta)
    flash_id = new_flash_id()
    audit_payload = {"flash_id": flash_id, "image": payload.patched_image, "vbmeta": payload.do_vbmeta, "ok": result["ok"]}
    return {"flash_id": flash_id, **result, "note": "Run steps on the operator PC via scripts/auto_flash.py — backend never injects shell."}


@router.post("/step")
async def step(payload: dict, request: Request, user=Depends(owner_only)):
    cmd = str(payload.get("cmd", ""))
    timeout = int(payload.get("timeout", 120))
    from app.services.flasher import run_step
    return run_step(cmd, timeout)


@router.get("/methods")
async def methods(user=Depends(owner_only)):
    from app.services.flasher import ALLOWED_STEPS
    return {"steps": [{"id": k, "cmd": c} for k, c in ALLOWED_STEPS]}
