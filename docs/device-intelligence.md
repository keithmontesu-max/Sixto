# Device Intelligence — Classification Rules

## Classification values (per exact model + firmware)

- `ROOTABLE` — verified procedure exists for exact model+firmware
- `NOT_ROOTABLE` — no verified procedure currently exists
- `BOOTLOADER_UNLOCKABLE` — legitimate supported unlock procedure exists
- `BOOTLOADER_LOCKED` — bootloader currently locked
- `AUTHORIZATION_REQUIRED` — manufacturer authorization required (e.g., Mi Unlock token)
- `PARTIALLY_SUPPORTED` — some services available, root/unlock not fully supported
- `UNKNOWN` — cannot reliably classify
- `EXCLUDED` — excluded by business policy

**Critical:** root eligibility and bootloader eligibility are SEPARATE fields.
A device can be bootloader-unlockable but have no verified root method, or vice versa.

## Manufacturers tracked
Samsung, Xiaomi, Redmi, POCO, Infinix, TECNO, Google Pixel, Motorola, OnePlus, Realme, OPPO, ASUS, Nothing, Sony, Nokia, Other.

No brand-level auto-support. Every record is per model identifier + hardware variant + chipset + Android/build fingerprint.

## Vivo policy
Vivo is **EXCLUDED** from the initial Auto Root service catalog. This is a product support restriction. Do **not** claim all Vivo devices are technically unrootable. The system must store this as manufacturer-level EXCLUDED with reason `BUSINESS_POLICY` and still allow exact-model evaluation for other services (diagnostics) where applicable.

## Compatibility record fields
manufacturer, model, model_id, hardware_variant, chipset, architecture, android_version, build_fingerprint, firmware_version, bootloader_status, unlock_eligible, root_eligible, supported_method, prerequisites, known_limitations, validation_status, last_tested_date, compatibility_release_version

Only `approved` records enable customer operations.

## Root managers
- **Magisk** — only when verified method exists
- **KernelSU** — only when kernel supports required implementation
- **APatch** — only when kernel+device satisfy requirements
- Others — admin approval + security review required

Installing manager APK ≠ working root. Four separate verifications: root implementation installed, kernel/boot compatibility, manager installed, actual root availability.
