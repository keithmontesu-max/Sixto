"""M8: release packaging + security checklist (documents the production gates).

Before production release, verify (each item has a backend enforcement):

1. Customers cannot access private tech console → OWNER-only routes 403 for customers (tests).
2. Technicians cannot get OWNER privileges → require_roles + server checks (tests).
3. Modified APKs cannot bypass backend auth → JWT + server-side role checks + audit.
4. Unapproved accounts cannot access private APIs → 401/403 (tests).
5. Unauthorized root workflows rejected → plan_operation + compatibility gate (tests).
6. Invalid update packages rejected → signature_hash required on releases; client must verify.
7. Incompatible managers blocked → select_root_manager never guesses (tests).
8. Suspicious uploads isolated → file type/size/scan queue (must wire with ClamAV/AV service before launch).
9. Bot abuse rate-limited → RateLimitMiddleware (login 10/min, register 5/min).
10. Revoked sessions blocked → is_active + locked_until checks on every request.
11. Owner-only ops need MFA → login requires TOTP when totp_enabled for privileged roles.
12. Sensitive ops audit-logged → OP_*, PAYMENT_*, COMPAT_*, RELEASE_*, CONFIG_* events.
13. Interrupted ops recover → operations are state machines (PLANNED→...→COMPLETED/FAILED); safe to re-plan.
14. App integrity checked → signed releases + integrity verification on update delivery.
15. Security failures alert → audit feed + /audit page + notifications on lockout.

Server hardening checklist:
- TLS everywhere; HSTS; CORS tightened to prod origins.
- Secrets via secret manager (never in APK/repo); rotate JWT secret + webhook secrets.
- Postgres backups encrypted; Redis not exposed; deps scanned (pip-audit).
- /docs disabled or authed in prod (set ENV=prod to hide).
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/release-checklist")
async def release_checklist():
    return {
        "version": "1.0.0",
        "notes": "See app/middleware/README for the 15 acceptance items.",
        "enforced_in_code": [
            "RBAC server-side + MFA for privileged roles",
            "Compatibility gate before ops",
            "HMAC webhook verification (fail closed)",
            "Rate limiting (login/register/webhook/API)",
            "Audit logs for all sensitive actions",
        ],
        "manual_gates": [
            "Upload malware scanning (ClamAV/AV) — wire before launch",
            "TLS + backup encryption + dep scan — infra",
            "Real-device test matrix walk (emulator ≠ physical)",
        ],
    }
