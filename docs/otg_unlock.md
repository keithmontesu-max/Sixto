# OTG Unlock (your rooted phone = PC)

## Setup (host, once)
```bash
pkg install -y root-repo
pkg install -y fastboot-android adb
su -c "python ~/sixto/backend/scripts/termux_console.py --port 8001"
```
Then open TECHTOOL → Console in the **same phone's browser**.

## Customer flow
```
Customer phone ──USB OTG── YOUR rooted phone (Termux)
  │  1. Customer taps "Allow USB debugging"
  │  2. Host: adb reboot bootloader
  │  3. Host: fastboot getvar unlocked (no)
  │  4. Host: fastboot flashing unlock → customer taps Vol+ UP
  │  5. Host: fastboot getvar unlocked (yes) → fastboot reboot
  └── Phone wipes + reboots
```

Customer phone needs **no Termux**. After unlock, install Magisk app on customer phone → patch + direct install (Termux Console: Detect → Verify patched → Install → Verify 4-check).

## Safety
- Customer consent required (`CUSTOMER YES` / Vol+ tap). FRP prompt = stop.
- One-shot shell alternative: `su -c "sh backend/scripts/termux_unlock.sh"` (same steps, no browser).
- Record stock boot SHA256 + build fingerprint before patching. Wrong build = bootloop.
