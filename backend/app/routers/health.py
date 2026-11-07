"""Health + monitoring endpoints."""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "db": db_ok,
        "env": settings.ENV,
        "redis_configured": bool(settings.REDIS_URL),
    }


@router.get("/health/ready")
async def ready(db: AsyncSession = Depends(get_db)):
    """Readiness for load-balancers (same as health, no auth)."""
    try:
        await db.execute(text("SELECT 1"))
        return {"ready": True}
    except Exception:
        return {"ready": False}
