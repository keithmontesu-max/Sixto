# SIXTO ROOT X — API Reference (base: /api/v1)

## Auth
- `POST /auth/register` — create customer account
- `POST /auth/login` — email+password (+TOTP for privileged roles)
- `POST /auth/refresh`
- `GET /auth/me` (includes prefs) | `POST /auth/prefs` | `POST /auth/deletion-request`
- `POST /auth/mfa/enable` | `POST /auth/mfa/disable`

## Devices
- `POST /devices` — register device (detection payload)
- `GET /devices/mine`

## Compatibility (Device Intelligence)
- `GET /compatibility/lookup?manufacturer=&model=&model_id=&firmware_line=` — returns separate root vs bootloader verdicts
- `GET /compatibility/admin/list` (OWNER/SUPER_ADMIN/ADMIN)
- `POST /compatibility/admin/upsert` (OWNER/SUPER_ADMIN/ADMIN)

## Services / Orders / Payments
- `GET /services` — active catalog (backend-driven prices)
- `POST /services/admin/upsert` | `GET /services/admin/all` | `POST /services/admin/{id}/toggle` (ADMIN+)
- `POST /orders` — create (idempotent)
- `GET /orders/mine` | `GET /orders/{id}` (fresh timeline + report)
- `GET /payments/methods` — owner-direct numbers (from BusinessConfig `payment_methods`)
- `POST /payments/initiate` (MANUAL|GCASH|MAYA|CARD + coupon) | `POST /payments/webhook/{provider}` (HMAC) | `POST /payments/admin/{id}/confirm|reject` (owner) | `GET /payments/history`
- `POST /coupons/validate` | `GET /coupons/admin/all` | `POST /coupons/admin/upsert`

## Operations (Auto Root orchestration)
- `GET /operations/methods`
- `POST /operations/plan` → `POST /operations/{id}/authorize` → `POST /operations/{id}/verify` (4 checks) → `GET /operations/{id}` | `GET /operations/history`

## Sessions / Remote
- `POST /sessions` — create pairing (returns 8-char code)
- `GET /sessions/{code}` | `POST /sessions/join` (technician)
- `GET /remote/sessions/mine` | `GET/POST /remote/sessions/{id}/messages`
- `WS /remote/sessions/ws/{code}?token=` — live relay (text/status/consent/diag)

## Notifications / Push / Templates
- `GET /notifications/mine` | `POST /notifications/{id}/read`
- `POST /push/register` | `GET /push/mine`
- `GET /templates` | `POST /templates` (ADMIN+)

## Technician
- `GET /technician/my-orders` | `POST /technician/orders/{id}/start|complete`

## Admin
- `GET /admin/overview?range=7d|30d|90d|today|yesterday`
- `GET /admin/audit?limit=` | `GET /admin/customers?q=` | `GET /admin/orders` | `GET /admin/payments/pending`
- `GET /admin/technicians` | `POST /admin/technicians` | `POST /admin/technicians/{id}/toggle` | `POST /admin/assign`
- `GET /admin/releases` | `POST /admin/releases` | `GET /admin/releases/active`
- `GET /admin/bugs` | `POST /admin/bugs` | `POST /admin/bugs/{id}/status`
- `GET /admin/finance` | `GET/POST /admin/config`

## Automation / Assistant / Tech (OWNER-only)
- `GET /automation/rules` | `POST /automation/run/assign|notify` (ADMIN+)
- `POST /assistant/ask` | `GET /assistant/demand`
- `GET /tech/status|diagnostics|incidents` | `POST /tech/emergency/disable-method|suspend-user|end-sessions` (**OWNER only — TECHTOOL**)
- `GET /release/release-checklist`

## Health
- `GET /health` — DB check
