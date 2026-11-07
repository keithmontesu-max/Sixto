# SIXTO ROOT X — Security Model

## Roles
OWNER > SUPER_ADMIN > ADMIN > TECHNICIAN > CUSTOMER
- Every privileged endpoint checks role server-side.
- Client-side checks are UX only; modified APKs get 401/403 from the backend.
- OWNER-only: private command engine, root method approval, engine deployment, emergency disable, security config.

## Auth
- Short-lived access tokens (15 min), rotating refresh tokens.
- MFA (TOTP) mandatory option for OWNER/SUPER_ADMIN/ADMIN.
- 5 failed logins -> 15-min lockout; all auth events audit-logged.
- No master passwords, signing keys, or payment secrets in the APK. Secrets via env/secret manager only.

## App protection (defense in depth)
- R8 obfuscation + removal of debug info in release builds.
- Signed releases, integrity checks, secure update validation.
- Server-controlled licensing: account + device registration, entitlement checks per request.
- Obfuscation is never the primary boundary — server-side checks are.

## Device operations
- No remote shell. Only predefined, typed, allowlisted operations.
- Each operation: unique ID, compatibility requirements, permissions, input validation, timeout, expected result, verification step, failure handling.
- Explicit customer consent before authorized execution; never blindly retry destructive ops.
- Never bypass FRP / anti-theft / account locks / manufacturer authorization.
- Consent screens explain bootloader-unlock consequences (data erasure, warranty).

## Payments
- Money state changes only on server-verified provider webhooks.
- Webhook signatures verified; duplicate `provider_ref` rejected (409); idempotency keys on orders.
- No raw card data stored; no paid status from screenshots.

## Uploads
- Type validation, size limits, malware-scan queue, isolated storage, hash verification for packages.

## Audits
- Login, failed auth, device registration, service requests, approvals, command execution, results, updates, permission changes, admin actions, license changes.
- No passwords/tokens/keys in logs.
