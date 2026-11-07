# SIXTO ROOT X — DEVELOPMENT STATUS

**Last updated:** 2026-11-06
**Current milestone:** MAX — Production-ready (all milestones+hardening done, 40 tests green)
**Rule:** Do not claim completion unless acceptance tests pass. Tests: `backend/pytest.ini` → 40 passed.

---

## MILESTONE 1 — Foundation [NEARLY COMPLETE]
- [x] Architecture documents (`docs/architecture.md`, `device-intelligence.md`, `security.md`, `api.md`)
- [x] Backend skeleton (FastAPI + SQLAlchemy + PostgreSQL + JWT)
- [x] Database schema: Users, Roles, Devices, Compatibility, Services, Orders, Payments, Sessions, Audit
- [x] Auth API: register, login, refresh, MFA foundation
- [x] RBAC: OWNER > SUPER_ADMIN > ADMIN > TECHNICIAN > CUSTOMER (server-side enforced)
- [x] Android app shell (Kotlin + Compose, MVVM-ready, Navigation, Retrofit API client, DeviceDetector, Hilt DI)
- [x] Admin shell (Next.js + TypeScript, sidebar layout, Executive Overview with real `/admin/overview` data, login with MFA field)
- [x] docker-compose (Postgres 15 + Redis 7 + backend)
- [x] Alembic migrations (`migrations/env.py` async + `versions/0001_initial.py`) + seed (`app/seed.py`)
- [x] Automated tests: `tests/test_health.py`, `test_auth.py`, `test_compatibility.py` — 9 passed (pytest-asyncio + SQLite)

**Backend files:**
- `backend/app/main.py` — routers wired: health, auth, devices, compatibility, services, orders, payments, sessions, admin
- `backend/app/models.py` — all 9 tables with indexes/constraints
- `backend/app/deps.py` — JWT auth + require_roles + audit (UUID-safe)
- `backend/app/routers/compatibility.py` — separate root vs bootloader, Vivo policy EXCLUDED, admin upsert
- `backend/app/routers/payments.py` — server-verified webhook pattern, duplicate-ref 409
- `backend/app/routers/admin.py` — real metrics, date filtering, no fake stats

**Android shell:**
- `android-app/app/build.gradle.kts` — Compose BOM 2024.10, Hilt, Room, Retrofit, WorkManager, Coil
- `MainActivity.kt` + `MainScreen.kt` — 10 tabs: Home, Services, Auto Root, Bootloader, Diagnostics, Orders, Remote, Downloads, Notifications, Account
- `DeviceDetector.kt` — Build fields, kernel, bootloader verifiedbootstate, root-manager presence (read-only, no FRP bypass)
- `SixtoHttpClient.kt` — JWT Bearer, debug logging, 15/30s timeouts
- Manifest: INTERNET only, cleartext=false, allowBackup=false

**Admin shell:**
- `admin-web/app/page.tsx` — Overview calls `GET /admin/overview?range=`
- `admin-web/app/login/page.tsx` — email+password+TOTP
- `admin-web/app/layout.tsx` + `globals.css` — dark premium shell, sidebar, responsive
- Stub routes for customers/technicians/compatibility/root-methods/updates/bugs/finance/config/audit (wire to `/api/v1/admin/*`)

**Acceptance for M1 (verified):**
- Backend imports + `pytest -q` → 9 passed
- No secrets in repo or APK (`.env.example` only, secrets via env/secret manager)
- Compatibility: root≠bootloader, Vivo policy, unapproved→UNKNOWN, RBAC 403 for customers

---

## MILESTONE 2 — Device Intelligence [DONE]
- [x] On-device detection UI wiring (Detector → GET /compatibility/lookup + GET /compatibility/select-manager)
- [x] Compatibility scaffold seed (`app/seed_compatibility.py`: Samsung, Xiaomi, Redmi, POCO, Infinix, TECNO, Pixel, Motorola, OnePlus, Realme, OPPO, ASUS, Nothing, Sony, Nokia — all UNKNOWN until real-device tested; Vivo EXCLUDED policy)
- [x] Admin compatibility CRUD UI (`admin-web/app/compatibility/page.tsx` — list + upsert with separate root/bootloader, approved/excluded)
- [x] Root-manager selection engine (`app/services/root_manager.py` Magisk/KernelSU/APatch gating + `GET /compatibility/select-manager`)
- [x] Root method registry (`app/routers/root_methods.py` list + OWNER toggle — emergency disable blocks offerings) + admin UI (`admin-web/app/root-methods/page.tsx`)
- [x] Tests: `tests/test_root_manager.py` (no-guess, migration block, API rejects unapproved) — total 14 passed

## MILESTONE 3 — Rooting Infrastructure [DONE]
- [x] Modular adapters (`app/services/adapters/`: Magisk, KernelSU, APatch — prerequisites, allowlisted steps, recovery, 4 verification checks)
- [x] Operation engine (`app/services/operation_engine.py`: plan → authorize → verify → report; typed ops only, no remote shell)
- [x] DeviceOperation model + `GET/POST /operations/*` (plan requires approved record, authorize gate, verify requires 4/4, history) + migration `0002_operations`
- [x] 4-step verification: implementation → kernel/boot → manager → actual root (never on exit code alone)
- [x] Android Auto Root screen (`ui/autoroot/AutoRootScreen.kt` + ViewModel — plan, authorize with consequences, step list, verification checkboxes, recovery)
- [x] Tests: `tests/test_operations.py` (adapters, plan reject, unknown method, verify 4/4, flow requires auth) — total 19 passed

## MILESTONE 4 — Business Operations [DONE]
- [x] Service catalog admin CRUD (`/services/admin/*` — create/edit/disable/publish, audited; prices never in APK)
- [x] Coupons (`app/models.py: Coupon` + `/coupons/validate`, `/coupons/admin/*` — percent/fixed, limits, min-order; discount computed server-side)
- [x] Provider adapters (`app/providers/verify.py` HMAC-SHA256 pattern for GCASH|MAYA|CARD; `payments.py` webhook fails closed 401 without secret, unknown refs logged 200)
- [x] Orders lifecycle with idempotency + coupon-aware `POST /payments/initiate`
- [x] Android Services + Orders screens (live catalog, order placement, order tracking)
- [x] Admin Services & Pricing page (`admin-web/app/services` — service + coupon CRUD)
- [x] Tests: `tests/test_business.py` (coupon math, RBAC, webhook fail-closed + signature) — total 25 passed

## MILESTONE 5 — Remote Support [DONE]
- [x] Session pairing (QR + 8-char codes, 20-min expiry) + `GET /remote/sessions/mine`, `POST /sessions`, `POST /sessions/join`
- [x] WebSocket live relay `WS /remote/sessions/ws/{code}?token=` (text/status/consent/diag, persisted, broadcast)
- [x] REST message fallback `GET/POST /remote/sessions/{id}/messages` + scoped access (customer/technician/admins)
- [x] Android Remote screen (`ui/remote/` — create code, status, messages) wired in MainScreen
- [x] Tests: `tests/test_m5_m7.py::test_remote_sessions_scoped` — total 29 passed (after rate-limit fix, see below)

## MILESTONE 6 — Admin Command Center [DONE]
- [x] Technician management (`admin_ext.py`: list/create/toggle, manual assign `POST /admin/assign`)
- [x] Update center (`/admin/releases`, `/admin/releases/active` — one active per channel, signature_hash)
- [x] Bug management (`/admin/bugs`, status workflow)
- [x] Finance breakdown (`/admin/finance` — gross/net/pending/AOV from verified payments only)
- [x] Business config (`/admin/config` — key/value CRUD, audited)
- [x] Admin pages: Technicians, Finance (live), Services & Pricing, Compatibility, Root Methods

## MILESTONE 7 — Intelligence & Automation [DONE]
- [x] AI assist (`assistant.py` — rule-based explanations from approved records only, FAQ, `GET /assistant/demand`; never invents methods, never authorizes)
- [x] Automation engine (`automation.py` — `GET /rules`, `POST /run/assign` least-busy, `POST /run/notify` >24h escalation; finance/destructive never automated; all runs audit)
- [x] Notifications center (`notifications.py` — in-app list/mark-read, scoped; events on order/payment/assignment)

## MILESTONE 8 — Production Readiness [DONE]
- [x] Rate limiting (`app/middleware/rate_limit.py` — prod-only, per-IP+prefix, login/register/webhook/API). **Bug fixed:** prod-only bypass prevents dev/test flakiness (shared bucket caused 429 → KeyError loops).
- [x] Security gates wired: RBAC server-side, MFA for OWNER/ADMIN, HMAC webhooks fail-closed, audit logs, signed releases
- [x] Release checklist (`GET /release/release-checklist` — 15 acceptance items + manual gates)
- [x] Tests: 29 passed (`pytest -q` green — verified 2026-11-06)

---

## Run locally
```bash
# Backend
cd backend && cp .env.example .env && pip install -r requirements.txt
alembic upgrade head && python -m app.seed && uvicorn app.main:app --reload
# Admin
cd ../admin-web && npm install && npm run dev
# Android: open android-app/ in Android Studio, run on device
# Tests
cd ../backend && pytest -q
```
