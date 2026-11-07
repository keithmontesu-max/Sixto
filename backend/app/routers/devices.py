"""Device registration + detection payload. Customer-scoped."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Device
from app.deps import get_current_user

router = APIRouter()


class DeviceIn(BaseModel):
    manufacturer: str
    model: str
    model_id: str = ""
    hardware_variant: str = ""
    chipset: str = ""
    android_version: str = ""
    kernel_version: str = ""
    build_fingerprint: str = ""
    bootloader_status: str = "UNKNOWN"
    is_rooted: bool = False
    root_manager: str = ""
    raw_data: dict = {}


@router.post("", status_code=201)
async def register_device(payload: DeviceIn, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    device = Device(user_id=user.id, **payload.model_dump())
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return {"id": str(device.id), "manufacturer": device.manufacturer, "model": device.model}


@router.get("/mine")
async def my_devices(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    result = await db.execute(select(Device).where(Device.user_id == user.id))
    return [{"id": str(d.id), "manufacturer": d.manufacturer, "model": d.model,
             "bootloader_status": d.bootloader_status, "is_rooted": d.is_rooted,
             "root_manager": d.root_manager, "android_version": d.android_version} for d in result.scalars()]
