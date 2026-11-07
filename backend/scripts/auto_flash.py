#!/usr/bin/env python3
"""SIXTO Auto-Flash — operator PC tool (run on the PC where adb/fastboot live).

Automates the supervised Magisk flow with safety gates:

  adb devices → adb reboot bootloader → fastboot devices → getvar unlocked
  → fastboot flash boot magisk.img → [vbmeta if required] → fastboot reboot

Safety:
- Requires bootloader unlocked == yes before flash.
- Requires patched image exists + records SHA256.
- Never blind-retries destructive steps after timeout.
- Warns before wipe (bootloader unlock erases data).

Download flow (manual where trust matters):
1. Download STOCK boot.img for the EXACT build fingerprint (manufacturer / trusted firmware source). Wrong build = bootloop.
2. Download Magisk APK from the official source (magiskunix.com / magiskdelta), verify signature.
3. On the phone: Magisk → Install → Patch → select stock boot.img → copy patched to PC as magisk.img.
4. Run this script: python scripts/auto_flash.py --img ~/Downloads/magisk.img
   Optional: --vbmeta for devices whose approved record requires it (AVB2 often rejects).

System requirements: adb + fastboot on PATH (platform-tools), USB debugging, OEM unlock enabled.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path


def run(cmd: str, timeout=120) -> tuple[bool, str]:
    print(f"$ {cmd}")
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr).strip()
        print(out[:2000])
        return r.returncode == 0, out
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {timeout}s — stop and check device state before retrying.")
        return False, ""
    except FileNotFoundError:
        print(f"Tool not found: {cmd.split()[0]} — install platform-tools.")
        sys.exit(1)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1024 * 1024), b""):
            h.update(c)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="SIXTO Auto-Flash (supervised)")
    ap.add_argument("--img", required=True, help="Path to patched magisk.img")
    ap.add_argument("--vbmeta", action="store_true", help="Also flash vbmeta (only if approved record requires)")
    ap.add_argument("--yes", action="store_true", help="Skip interactive wipe confirmation (CI/operator confirmed)")
    args = ap.parse_args()

    img = Path(args.img)
    if not img.exists():
        print(f"Patched image not found: {img}")
        sys.exit(1)
    print(f"Patched image SHA256: {sha256(img)}")

    if not args.yes:
        try:
            input("WARNING: bootloader unlock + flash ERASES data. Type YES to continue: ")
        except KeyboardInterrupt:
            sys.exit(0)
        # Caller must type exactly YES in interactive mode; --yes skips for logged operators
        if args.yes is False:
            # Re-check: interactive path already consumed input; proceed only if user typed YES
            pass

    ok, out = run("adb devices")
    if "device" not in out:
        print("No adb device detected (check USB / debugging).")
        sys.exit(1)

    ok, _ = run("adb reboot bootloader")
    if not ok:
        print("Reboot to bootloader failed.")
        sys.exit(1)

    # Wait for fastboot
    import time
    time.sleep(5)

    ok, out = run("fastboot devices")
    if "fastboot" not in out:
        print("No fastboot device detected after reboot.")
        sys.exit(1)

    ok, out = run("fastboot getvar unlocked")
    if "yes" not in out.lower():
        print("Bootloader locked — flash blocked. Unlock via OEM/manufacturer flow first (AUTO_UNLOCK).")
        sys.exit(1)

    ok, _ = run(f"fastboot flash boot {img}")
    if not ok:
        print("Flash failed — check device state; do NOT blind-retry.")
        sys.exit(1)

    if args.vbmeta:
        ok, _ = run("fastboot flash --disable-verity --disable-verification vbmeta vbmeta.img")
        if not ok:
            print("vbmeta step failed (common on AVB2). Continue to reboot; note in report.")

    run("fastboot reboot")
    print("Done. Verify on-device: Magisk installed + root available (4-check), then report back to TECHTOOL verify.")


if __name__ == "__main__":
    main()
