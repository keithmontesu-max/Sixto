#!/usr/bin/env python3
"""SIXTO Termux Console — on-device runner for TECHTOOL Console (rooted phone).

Run in Termux (on the phone you own):
    su
    python ~/sixto/backend/scripts/termux_console.py --port 8001

Then open TECHTOOL → Console in the same phone's browser.
Console talks to http://127.0.0.1:8001 (same phone). Allowlisted only:
  GET  /status     {manufacturer, model, fingerprint, bootloader, is_rooted}
  POST /run        {"id": "detect|patch_verify|install|verify|otg_devices|otg_reboot|otg_getvar|otg_unlock|otg_verify"}  (timed, logged)
  GET  /log        last 200 lines

OTG mode (host=your phone, target=customer phone via USB):
  otg_devices → adb devices (customer taps Allow)
  otg_reboot → adb reboot bootloader
  otg_getvar → fastboot getvar unlocked
  otg_unlock → fastboot flashing unlock (customer taps Vol+)
  otg_verify → fastboot getvar unlocked again

Safety:
- No arbitrary shell. Only fixed ids below.
- Patch/install require stock + patched images present (you place them via Magisk).
- Reboot is NOT automated here (kills server) — step tells you to reboot, then Verify.
"""
import json
import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

LOG: list[str] = []

def log(msg: str):
    LOG.append(f"[{time.strftime('%H:%M:%S')}] {msg}")
    if len(LOG) > 200:
        LOG.pop(0)
    print(LOG[-1])

def sh(cmd: str, timeout=30) -> str:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout + r.stderr).strip()
        return out or f"(exit {r.returncode})"
    except subprocess.TimeoutExpired:
        return f"TIMEOUT after {timeout}s"
    except Exception as e:
        return f"ERR: {e}"

def status() -> dict:
    return {
        "manufacturer": sh("getprop ro.product.manufacturer | head -1"),
        "model": sh("getprop ro.product.model | head -1"),
        "fingerprint": sh("getprop ro.build.fingerprint | head -1"),
        "bootloader": sh("getprop ro.boot.verifiedbootstate; getprop ro.boot.flash.locked"),
        "is_rooted": sh("su -c 'id -u 2>/dev/null || echo no'"),
    }

def run_step(sid: str) -> dict:
    log(f"RUN {sid}")
    if sid == "detect":
        return {"ok": True, "result": status()}
    if sid == "patch_verify":
        out = sh("ls -lh ~/patched/magisk.img /sdcard/Download/magisk_patched.img 2>&1; sha256sum ~/patched/magisk.img /sdcard/Download/magisk_patched.img 2>&1 | head -4")
        return {"ok": "/sdcard/Download" in out or "patched" in out, "result": out}
    if sid == "install":
        # Magisk direct install must be tapped in the Magisk app (no headless flash).
        return {"ok": True, "result": "Open Magisk app → Install → Direct install → reboot. This step cannot be headless; console guides you."}
    if sid == "verify":
        out = sh("su -c 'magisk --version 2>&1; magisk --list-modules 2>&1 | head -5; ls /sbin/.magisk 2>&1; magisk --check-su 2>&1 | head -3'")
        return {"ok": "magisk" in out.lower(), "result": out}
    if sid == "otg_devices":
        out = sh("adb devices 2>&1")
        return {"ok": "device" in out, "result": out}
    if sid == "otg_reboot":
        out = sh("adb reboot bootloader 2>&1")
        return {"ok": out == "" or "error" not in out.lower(), "result": out + "\n\nWait 5s, then tap otg_getvar."}
    if sid == "otg_getvar":
        out = sh("fastboot devices 2>&1; fastboot getvar unlocked 2>&1 | head -5")
        return {"ok": "fastboot" in out.lower(), "result": out}
    if sid == "otg_unlock":
        out = sh("fastboot flashing unlock 2>&1")
        return {"ok": "ok" in out.lower() or out == "", "result": out + "\n\nOn CUSTOMER phone: tap Volume UP to confirm."}
    if sid == "otg_verify":
        out = sh("fastboot getvar unlocked 2>&1 | head -5")
        return {"ok": "unlocked: yes" in out.lower(), "result": out}
    return {"ok": False, "result": "Unknown step (allowlisted only)"}

class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/status":
            return self._json(200, status())
        if self.path == "/log":
            return self._json(200, {"log": LOG})
        return self._json(404, {"error": "not found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode())
        except Exception:
            return self._json(400, {"error": "bad json"})
        if self.path == "/run":
            sid = str(body.get("id", ""))
            if sid not in ("detect", "patch_verify", "install", "verify", "otg_devices", "otg_reboot", "otg_getvar", "otg_unlock", "otg_verify"):
                return self._json(400, {"error": "step not allowlisted"})
            return self._json(200, run_step(sid))
        return self._json(404, {"error": "not found"})

    def log_message(self, *args):
        pass

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8001)
    a = ap.parse_args()
    log(f"Termux Console on :{a.port} — open TECHTOOL → Console in this phone's browser")
    HTTPServer(("127.0.0.1", a.port), Handler).serve_forever()
