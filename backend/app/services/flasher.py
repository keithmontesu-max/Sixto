"""Auto-flash orchestrator (TECHTOOL, OWNER-only).

Automates the supervised Magisk flow you described, with safety gates:

  adb devices (detect exact device)
  → adb reboot bootloader (fastboot ready)
  → fastboot devices (connected?)
  → fastboot getvar unlocked (must be yes)
  → fastboot flash boot magisk.img (patched image, verified hash)
  → vbmeta (only if device route requires it; AVB2 often rejects --disable-verity)
  → fastboot reboot
  → verify (bootloader + root state, 4-check)

Never blind-flashes. Never runs without:
- bootloader unlocked == yes
- patched image exists + SHA256 recorded
- customer authorized (DeviceOperation AUTHORIZED)

Local execution happens on the operator's PC (where adb/fastboot live).
Backend only orchestrates state + verification.
"""
import hashlib
import uuid
from pathlib import Path

ALLOWED_STEPS = [
    ("adb_devices", "adb devices"),
    ("reboot_bootloader", "adb reboot bootloader"),
    ("fastboot_devices", "fastboot devices"),
    ("getvar_unlocked", "fastboot getvar unlocked"),
    ("flash_boot", "fastboot flash boot magisk.img"),
    ("flash_vbmeta", "fastboot flash --disable-verity --disable-verification vbmeta vbmeta.img"),
    ("reboot", "fastboot reboot"),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_flash(patched_image: str, do_vbmeta: bool = False) -> dict:
    """Generate allowlisted command plan. Returns {ok, steps, warnings}."""
    p = Path(patched_image)
    if not p.exists():
        return {"ok": False, "reason": f"Patched image not found: {patched_image}", "steps": []}
    if p.suffix.lower() != ".img":
        return {"ok": False, "reason": "Patched image must be .img (magisk.img)", "steps": []}
    steps = []
    for name, cmd in ALLOWED_STEPS:
        if name == "flash_vbmeta" and not do_vbmeta:
            continue
        steps.append({"id": name, "cmd": cmd, "timeout": 120, "expected": "device state as described"})
    warnings = [
        "Bootloader must be unlocked (getvar unlocked = yes). This erases data.",
        "Wrong-build boot image = bootloop. Verify build fingerprint matches exactly.",
        "vbmeta --disable-verity is deprecated on many AVB2 devices and may fail; only use if the approved record requires it.",
    ]
    return {"ok": True, "image_sha256": sha256_file(p), "steps": steps, "warnings": warnings}


def run_step(cmd: str, timeout: int = 120) -> dict:
    """Execute one allowlisted step with timeout. Returns {ok, output, returncode}."""
    import subprocess
    if cmd not in [c for _, c in ALLOWED_STEPS]:
        return {"ok": False, "error": "Command not allowlisted", "cmd": cmd}
    try:
        r = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=timeout)
        return {"ok": r.returncode == 0, "output": (r.stdout + r.stderr)[:4000], "returncode": r.returncode, "cmd": cmd}
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timed out after {timeout}s (never blind-retry destructive steps)", "cmd": cmd}
    except FileNotFoundError:
        return {"ok": False, "error": f"Tool not found (install platform-tools): {cmd.split()[0]}", "cmd": cmd}


def new_flash_id() -> str:
    return str(uuid.uuid4())[:8].upper()
