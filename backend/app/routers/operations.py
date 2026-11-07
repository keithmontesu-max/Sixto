"""Device operations API — plan → authorize → verify → report.

Local execution happens on-device via the customer's explicit authorization;
this API orchestrates state, consent, and verification. No remote shell.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Device, DeviceOperation, Order
from app.deps import get_current_user, audit
from app.services.operation_engine import plan_operation, verify_operation
from app.routers.compatibility import classify_record
from app.models import CompatibilityRecord

router = APIRouter()


class PlanIn(BaseModel):
    device_id: str
    method: str = ""  # empty = auto-select; BOOTLOADER_UNLOCK = bootloader op
    order_id: str = ""


class VerifyIn(BaseModel):
    implementation_installed: bool = False
    kernel_boot_compatible: bool = False
    manager_installed: bool = False
    actual_root_available: bool = False
    bootloader_unlocked: bool = False
    wipe_acknowledged: bool = False
    authorization_completed: bool = False
    notes: str = ""


def _get_compat(db, device: Device):
    # Exact lookup by manufacturer+model (model_id when present).
    q = select(CompatibilityRecord).where(
        CompatibilityRecord.manufacturer.ilike(device.manufacturer),
        CompatibilityRecord.model.ilike(device.model),
    )
    if device.model_id:
        q = q.where(CompatibilityRecord.model_id.ilike(device.model_id))
    else:
        q = q.where(CompatibilityRecord.model_id == "")
    return q


@router.get("/methods")
async def methods(user=Depends(get_current_user)):
    from app.services.operation_engine import available_methods
    return {"methods": available_methods()}


@router.post("/plan", status_code=201)
async def plan(payload: PlanIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        dev_id = uuid.UUID(payload.device_id)
    except (ValueError, TypeError):
        raise HTTPException(400, "Invalid device id")
    dev = (await db.execute(select(Device).where(Device.id == dev_id, Device.user_id == user.id))).scalar_one_or_none()
    if not dev:
        raise HTTPException(404, "Device not registered to your account")

    rec = (await db.execute(_get_compat(db, dev))).scalar_one_or_none()
    if not rec:
        raise HTTPException(400, "No compatibility record. Run device intelligence first; diagnostics only.")

    compat = classify_record(rec)
    method = payload.method or compat.get("supported_method") or ""
    plan_result = plan_operation(method, compat)
    if not plan_result["ok"]:
        raise HTTPException(400, plan_result["reason"])

    steps = [{"name": s["name"], "description": s["description"], "destructive": s["destructive"],
              "expected_result": s["expected_result"], "verification": s["verification"],
              "timeout_seconds": s["timeout_seconds"], "status": "PENDING"} for s in plan_result["steps"]]

    order_uuid = None
    if payload.order_id:
        try:
            order_uuid = uuid.UUID(payload.order_id)
        except (ValueError, TypeError):
            raise HTTPException(400, "Invalid order id")
        o = (await db.execute(select(Order).where(Order.id == order_uuid, Order.user_id == user.id))).scalar_one_or_none()
        if not o:
            raise HTTPException(404, "Order not found")

    op = DeviceOperation(user_id=user.id, device_id=dev_id, order_id=order_uuid,
                         operation_type="BOOTLOADER" if plan_result["method"] == "BOOTLOADER_UNLOCK" else "ROOT",
                         method=plan_result["method"],
                         status="AWAITING_AUTH" if plan_result["requires_authorization"] else "AUTHORIZED",
                         steps=steps, verification={})
    db.add(op)
    audit(db, user.id, "OP_PLAN", "operation", op.id, request.client.host, {"method": op.method})
    await db.commit()
    await db.refresh(op)
    return {"id": str(op.id), "method": op.method, "status": op.status,
            "prerequisites": plan_result["prerequisites"], "steps": steps,
            "recovery": plan_result["recovery"], "verification_checks": plan_result["verification_checks"]}


@router.post("/{operation_id}/authorize")
async def authorize(operation_id: str, request: Request, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        oid = uuid.UUID(operation_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Operation not found")
    op = (await db.execute(select(DeviceOperation).where(DeviceOperation.id == oid, DeviceOperation.user_id == user.id))).scalar_one_or_none()
    if not op:
        raise HTTPException(404, "Operation not found")
    if op.status not in ("PLANNED", "AWAITING_AUTH"):
        raise HTTPException(400, f"Cannot authorize from status {op.status}")
    op.authorized_by_customer = True
    op.status = "AUTHORIZED"
    audit(db, user.id, "OP_AUTHORIZE", "operation", op.id, request.client.host)
    await db.commit()
    return {"id": str(op.id), "status": op.status, "authorized": True,
            "message": "Authorized. On-device execution may proceed via allowlisted ops."}


@router.post("/{operation_id}/verify")
async def verify(operation_id: str, payload: VerifyIn, request: Request, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        oid = uuid.UUID(operation_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Operation not found")
    op = (await db.execute(select(DeviceOperation).where(DeviceOperation.id == oid, DeviceOperation.user_id == user.id))).scalar_one_or_none()
    if not op:
        raise HTTPException(404, "Operation not found")
    if op.status not in ("AUTHORIZED", "EXECUTING", "VERIFYING"):
        # Allow verifying after authorize even if client skipped to verify (test harness).
        if op.status in ("PLANNED", "AWAITING_AUTH"):
            raise HTTPException(400, "Operation must be authorized before verification")
    from app.services.operation_engine import verify_operation, verify_bootloader
    if op.operation_type == "BOOTLOADER":
        result = verify_bootloader(payload.model_dump())
    else:
        result = verify_operation(payload.model_dump())
    op.verification = {**result, "notes": payload.notes}
    op.status = "COMPLETED" if result["success"] else "FAILED"
    if not result["success"]:
        op.failure_reason = result["verdict"]
    audit(db, user.id, "OP_VERIFY", "operation", op.id, request.client.host, {"success": result["success"]})
    await db.commit()
    return {"id": str(op.id), "status": op.status, **result}


@router.get("/{operation_id}")
async def get_operation(operation_id: str, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    try:
        oid = uuid.UUID(operation_id)
    except (ValueError, TypeError):
        raise HTTPException(404, "Operation not found")
    op = (await db.execute(select(DeviceOperation).where(DeviceOperation.id == oid, DeviceOperation.user_id == user.id))).scalar_one_or_none()
    if not op:
        raise HTTPException(404, "Operation not found")
    return {"id": str(op.id), "method": op.method, "status": op.status,
            "steps": op.steps, "verification": op.verification,
            "failure_reason": op.failure_reason, "authorized": op.authorized_by_customer}


@router.get("/history")
async def history(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(DeviceOperation).where(DeviceOperation.user_id == user.id).order_by(DeviceOperation.created_at.desc()).limit(50))
    return [{"id": str(o.id), "method": o.method, "status": o.status, "created_at": str(o.created_at)} for o in result.scalars()]
