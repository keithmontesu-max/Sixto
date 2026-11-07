# SIXTO ROOT X — Production Runbook (direct-payment model)

## 1. Configure your payment numbers (once)
In Admin → Business Config, save key `payment_methods`:
```json
{"gcash_number":"09XXXXXXXXX","gcash_name":"Your Name","maya_number":"09XXXXXXXXX","maya_name":"Your Name","instructions":"Pay the owner directly, then submit your transaction reference in the app."}
```
App reads this from `GET /payments/methods`. No APK update needed. Change numbers anytime.

## 2. Daily ops
- Admin → Orders & Payments: see PENDING refs → verify in your GCash/Maya app → Confirm/Reject.
- Auto-assign: `POST /automation/run/assign` (least-busy tech) + `POST /automation/run/notify` (24h escalation).
- Admin → Compatibility: approve records only after real-device testing. Unapproved = UNKNOWN.
- Admin → Root Methods: Disable immediately if a method has a security issue.
- Admin → Releases: publish signed releases (one active per channel).

## 3. Booking flow (customer)
Services → pick device → Order → Pay owner directly → Submit ref in app → Owner confirms → Technician assigned → Remote code → Authorize ops → Verified → Completion report.

## 4. Security gates (enforced in code)
- JWT + MFA (OWNER/ADMIN) + lockout + audit on every sensitive action
- Webhooks HMAC verify (fail-closed); manual confirms audited
- Allowlisted ops only; destructive steps need explicit customer authorize
- 4-step root verification (never on exit code alone)

## 5. Launch checklist
- [ ] Postgres + Redis hosted, backups encrypted
- [ ] `ENV=prod`, strong `JWT_SECRET`, `PAY_WEBHOOK_SECRET_*` in secret manager
- [ ] CORS tightened to your domains, TLS everywhere
- [ ] FCM/SMTP env set for push/email (else log-only)
- [ ] Real-device matrix walked (emulator ≠ physical)
- [ ] `GET /release/release-checklist` green
