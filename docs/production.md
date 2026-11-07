# SIXTO ROOT X — Production Deployment (step-by-step)

## Prerequisites
- Linux VPS (2 vCPU / 4GB) or container host
- Domain + TLS (Let's Encrypt / Cloudflare Tunnel)
- Postgres 15 + Redis 7 (or `docker compose` local)
- Node 20 for builds, Python 3.12 for backend

## 1. Backend
```bash
cd backend
cp .env.example .env   # edit: DATABASE_URL, REDIS_URL, JWT_SECRET (32+ chars), CORS_ORIGINS (prod domains), ENV=prod
pip install -r requirements.txt
alembic upgrade head
python -m app.seed && python -m app.seed_compatibility
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Set `CORS_ORIGINS` to `https://admin.yourdomain.com,https://app.yourdomain.com` (no localhost in prod).

## 2. Admin (:3000) + TECHTOOL (:3001)
```bash
cd admin-web && npm ci && npm run build && npm start
cd ../techtool && NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1 npm run build && npm start
```
Or `docker compose up --build` (all three + db/redis).

## 3. Payments (direct model)
- Admin → Business Config: save `payment_methods` JSON with your GCash/Maya numbers.
- Customer pays you directly → submits ref → you verify in wallet → Orders tile Confirm.
- Optional gateway: set `PAY_WEBHOOK_SECRET_GCASH/MAYA/CARD` + implement provider canonicalization in `app/providers/verify.py`.

## 4. Push/email (optional mirrors)
- `FCM_SERVER_KEY`, `MAIL_HOST/PORT/USER/PASS/FROM` in env. No config = log-only, never crashes.

## 5. Security gates before launch
- `GET /health` → `{"status":"ok","db":true}`
- `GET /release/release-checklist` → review manual gates
- `python -m app.checklist` → counts sanity
- `pytest -q` → 38 passed (run locally before push)
- OWNER MFA: `POST /auth/mfa/enable` → scan QR → verify `totp_enabled`
- TLS + HSTS (middleware already sets HSTS on HTTPS), Postgres backups encrypted

## 6. Android release
- `android-app/app/build.gradle.kts`: set `API_BASE_URL` to `https://api.yourdomain.com/api/v1/`, enable R8 (`isMinifyEnabled=true`), sign with release keystore (CI secret), test on **physical devices** per `docs/device-test-matrix.md`.
