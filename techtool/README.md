# SIXTO TECHTOOL — Owner-Only Engine (separate from customer app)

**Not the customer app. Not the admin dashboard. This is the private engine.**

## Separation architecture

```
Customer Android APK   ──►  /api/v1/auth|devices|compatibility|services|orders|payments/sessions
                              (customer-scoped, cannot import tech router)

Admin Web (operator)   ──►  /api/v1/admin|templates|config (ADMIN ok)

TECHTOOL (this folder) ──►  /api/v1/tech/*  (OWNER ONLY, MFA enforced at login)
                              Customer/technician tokens → 403. Modified APK → 403.
```

- **This folder builds separately:** `techtool/` is its own Next.js app (port 3001). It never ships inside the customer APK (no private scripts, no engine config, no secret URLs in the APK).
- **Server is the lock:** every `/tech/*` route does `require_roles("OWNER")`. Hiding a button is not security — the backend rejects.
- **Owner login** requires `OWNER` role + TOTP when enabled (`POST /auth/login` with `totp_code`). Set it up via `POST /auth/mfa/enable`.

## What TECHTOOL does (godly features live here)

- Engine status (users, compat counts, active sessions)
- Emergency: disable a root method platform-wide, suspend a user, end all live sessions
- Diagnostics (compat by class), Security incidents (failed auth + engine actions from audit)

Customer Auto Root still runs in the customer app, but only against **approved** records. TECHTOOL is where you approve/disable methods, not where customers click.

## Run

```bash
cd techtool
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 npm run dev  # :3001
```

## Security rules

- Never share OWNER credentials. MFA mandatory for production.
- Rotate `JWT_SECRET` + webhook secrets via secret manager.
- Every TECHTOOL action is audit-logged (`ENGINE_*`).
