"""SIXTO ROOT X — Backend entrypoint (System C)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from app.config import settings
from app.routers import auth, devices, compatibility, services, orders, admin, payments, sessions, health, root_methods, operations, coupons, remote, notifications, admin_ext, automation, assistant, release, templates, technician, push, tech, tech_analyze, flash
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(
    title="SIXTO ROOT X API",
    version="1.0.0",
    description="Commercial Android rooting intelligence + remote services platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)
# Tighten in production: allowed_hosts=["api.sixto.example.com"]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])
app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(devices.router, prefix="/api/v1/devices", tags=["devices"])
app.include_router(compatibility.router, prefix="/api/v1/compatibility", tags=["compatibility"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"])
app.include_router(root_methods.router, prefix="/api/v1/root-methods", tags=["root-methods"])
app.include_router(operations.router, prefix="/api/v1/operations", tags=["operations"])
app.include_router(coupons.router, prefix="/api/v1/coupons", tags=["coupons"])
app.include_router(remote.router, prefix="/api/v1/remote", tags=["remote"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["notifications"])
app.include_router(admin_ext.router, prefix="/api/v1/admin", tags=["admin-ext"])
app.include_router(automation.router, prefix="/api/v1/automation", tags=["automation"])
app.include_router(assistant.router, prefix="/api/v1/assistant", tags=["assistant"])
app.include_router(release.router, prefix="/api/v1/release", tags=["release"])
app.include_router(templates.router, prefix="/api/v1/templates", tags=["templates"])
app.include_router(technician.router, prefix="/api/v1/technician", tags=["technician"])
app.include_router(push.router, prefix="/api/v1/push", tags=["push"])
app.include_router(tech.router, prefix="/api/v1/tech", tags=["tech-owner-only"])
app.include_router(tech_analyze.router, prefix="/api/v1/tech", tags=["tech-analyze"])
app.include_router(flash.router, prefix="/api/v1/flash", tags=["flash-owner-only"])


@app.get("/")
def root():
    return {"service": "SIXTO ROOT X", "status": "ok", "docs": "/docs"}
