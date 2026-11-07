# Device Test Matrix — real hardware only (emulator ≠ validation)

| Manufacturer | Model | Model ID | Variant | Android | Build FP | Root (manager) | Bootloader | Tested by | Date | Result |
|---|---|---|---|---|---|---|---|---|---|---|
| Samsung | Galaxy A54 | a54x | — | 14 | ... | Magisk / UNKNOWN | LOCKED |  |  |  |
| Xiaomi | Redmi Note 12 | sky | — | 13 | ... | UNKNOWN | UNKNOWN |  |  |  |

**Rules:**
- Only `approved` records in the DB enable Auto Root. A matrix row is *evidence*, not approval — OWNER approves in Admin → Compatibility after review.
- Record `last_tested_date` + `release_version` on the compatibility record.
- If a method fails on re-test, set `is_approved=false` or disable the method in TECHTOOL immediately.
- Distinguish emulator tests (CI, SQLite) from **physical device** validation (this matrix + `last_tested_date`).

## Process
1. Seed scaffold (`python -m app.seed_compatibility`) → all UNKNOWN.
2. Test on physical device (Detector → Lookup → Plan → Authorize → Verify 4/4).
3. Admin approves exact record with prerequisites/limits.
4. Customer sees automated workflow; otherwise diagnostics only.
