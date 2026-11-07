# SIXTO ROOT X — Architecture

## Systems

**A. Customer Android App** — Kotlin, Jetpack Compose, MVVM/Clean, Room, Hilt, Retrofit/Ktor, WorkManager, DataStore
**B. Admin Web** — Next.js (TypeScript), server-side authorization checks, charting, data tables
**C. Backend** — FastAPI, PostgreSQL 15+, Redis, SQLAlchemy, Alembic, Uvicorn, WebSockets
**D. Device Intelligence** — Detection engine + compatibility DB + root adapters (Magisk/KernelSU/APatch)

## API principles
- REST for CRUD, WebSocket for sessions/notifications/progress
- Short-lived access tokens (15 min) + rotating refresh tokens
- Every privileged endpoint checks role server-side; client-side role checks are UX only
- Money movement only on server-verified payment events
- Device operations only via allowlisted typed operations with explicit customer consent
- All sensitive actions write audit logs (no passwords/tokens in logs)

## Database isolation
- Customer data isolation via user_id scoping on every query
- Financial tables use transactions + idempotency keys
- Compatibility records require `approved` status before customer operations

## Security (defense in depth)
- MFA (TOTP) for OWNER/SUPER_ADMIN/ADMIN
- Rate limiting + lockout + suspicious-login detection
- TLS everywhere, secrets via environment / secret manager (never in APK)
- Signed updates (app + compatibility manifests), integrity verification
- R8 obfuscation as secondary layer only — real security is server-side
- File uploads: type validation, size limits, malware scan queue, isolated storage

## Scalability
- Pagination everywhere, caching for catalog/compatibility reads, background jobs for notifications/webhooks, connection pooling
- Stateless API tier for horizontal scaling
