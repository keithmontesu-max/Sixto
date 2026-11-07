# SIXTO ROOT X — Admin Command Center (System B)

Next.js (TypeScript) + responsive component system. Desktop-first with mobile support.

## Pages
```
/login                      # MFA required for privileged roles
/                          # Executive overview (real backend metrics, date filtering: today/yesterday/7d/30d/90d/custom)
/customers                  # Search, profiles, devices, orders, payments, tickets, account status
/technicians                # Accounts, roles, order assignment, workload, ratings, suspension
/compatibility              # Add/edit/approve models, firmware variants, rootability, unlock eligibility, exclusions
/root-methods               # Registry: supported devices, firmware, prerequisites, version, security review, deprecation
/updates                    # App/backend/DB/rule releases: versioning, staged rollout, rollback, history
/bugs                       # Crash/error reports by device+firmware, severity, assignment, fix tracking
/finance                    # Gross/net revenue, refunds, pending, per-service/technician, AOV, export
/config                     # Branding, services, pricing, currency, support info, policies, templates, hours
/audit                      # Security events: failed logins, abuse, integrity failures, incidents
```

## Rules
- All data from backend APIs (no hardcoded stats).
- Server-side authorization on every API call; UI role checks are UX only.
- Every sensitive action requires confirmation + writes audit log (backend enforces).
- OWNER-only sections (command engine, method approval) hidden from non-OWNER roles AND rejected server-side.
