# SIXTO ROOT X

Premium Android rooting intelligence + remote device service business platform.

**Tagline:** ROOTING INTELLIGENCE × REMOTE SERVICES × BUSINESS AUTOMATION

## Product Architecture (3 apps, 1 backend)

```
┌─────────────────────────────────────────────────────────┐
│ CUSTOMER APPS (clean, no engine)                        │
│  Android (android-app) : Home, Services, Auto Root,     │
│    Bootloader, Diagnostics, Orders, Remote, Downloads   │
│  Admin Web (admin-web) : Orders, Finance, Compat,       │
│    Technicians, Config, Templates, Tech Portal          │
└──────────────────────────┬──────────────────────────────┘
                           │ REST / WebSocket (customer token)
┌──────────────────────────▼──────────────────────────────┐
│ Backend (FastAPI + PostgreSQL) — browser of truth       │
│  Auth/MFA, Compatibility, Services, Orders, Payments,   │
│  Operations, Remote WS, Notifications, Automation       │
└──────────────────────────┬──────────────────────────────┘
                           │ OWNER token only
┌──────────────────────────▼──────────────────────────────┐
│ TECHTOOL (techtool/) — Owner-Only Engine :3001         │
│  Engine status, emergency disable, security incidents   │
│  Customer APK gets 403 on /tech/* (server-side)         │
└─────────────────────────────────────────────────────────┘
```

**Direct payments:** customer pays OWNER's GCash/Maya (numbers from `BusinessConfig payment_methods`), submits ref in My Orders → detail, owner verifies in wallet → `POST /payments/admin/{id}/confirm` → auto-assign. No gateway holds money. See `docs/runbook.md`.

## Core Principles

1. **Technical honesty** - Never advertise a device as rootable based on brand alone. Classification is per exact model + firmware variant.
2. **Separate eligibility** - Root eligibility and bootloader unlock eligibility are independent fields.
3. **Vivo policy** - Vivo is EXCLUDED from the initial Auto Root catalog (business restriction, not a technical claim). The catalog must allow manufacturer-level exclusion while keeping exact-model evaluation for supported brands.
4. **Verified operations only** - Never report success on exit code alone. Verify actual device state (root presence, bootloader state).
5. **Owner-controlled technology** - Private tech engine is owner-only, server-side authorized, MFA-protected. No client-side trust.
6. **Real commerce** - No hardcoded prices. All services, pricing, coupons, and policies come from backend.

## Repo Layout

```
SIXTO_ROOT_X/
├── backend/               # FastAPI (all APIs, 35 tests)
├── android-app/           # Customer app (clean, no engine)
├── admin-web/             # Operator desk (:3000)
├── techtool/              # Owner Engine (:3001, OWNER-only)
├── docs/
│   ├── architecture.md
│   ├── device-intelligence.md
│   ├── security.md
│   ├── api.md
│   ├── runbook.md         # Direct-payment ops + launch checklist
│   └── push-setup.md      # FCM/SMTP setup
├── docker-compose.yml
├── DEVELOPMENT_STATUS.md
└── README.md
```

## Quick Start (Milestone 1)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # configure DATABASE_URL, JWT_SECRET
uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

**Admin:**
```bash
cd admin-web
npm install
npm run dev
# http://localhost:3000
```

**Android:**
Open `android-app/` in Android Studio (Arctic Fox+). Sync Gradle, run on device/emulator.
API base URL configured via build variant `API_BASE_URL` (BuildConfig).

See `DEVELOPMENT_STATUS.md` for milestone checklist and acceptance tests.
