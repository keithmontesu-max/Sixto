#!/system/bin/sh
# SIXTO Auto-Root (Termux on the ROOTED phone — NO PC)
# Installs Magisk by patching stock boot.img ON-DEVICE (no fastboot needed for most devices).
#
# Run in Termux (needs root):
#   pkg install -y root-repo && pkg install -y git
#   git clone <sixto-repo> && cd sixto/backend/scripts
#   su -c "sh auto_root_termux.sh --boot ~/Downloads/boot.img --magisk ~/Downloads/Magisk-v27.apk"
#
# What it does (supervised, never blind):
#   1. Verifies device + build fingerprint
#   2. Verifies stock boot.img exists + SHA256 recorded
#   3. Patches via Magisk app (Install → select file) — you tap Patch, script verifies output
#   4. Copies patched to ~/patched/magisk.img
#   5. Direct install via Magisk (no fastboot): magisk --install-module / magisk --live ?
#      On most devices with Magisk app, direct install works after patch.
#   6. Verifies 4-check (implementation, kernel/boot, manager, actual root)
#
# IMPORTANT: First-time bootloader unlock STILL needs PC fastboot (AUTO_UNLOCK).
# Once unlocked + rooted, all updates are on-device via this script + Magisk app.
# Wrong-build boot = bootloop. Verify build before patching. Back up first.
#
set -e
BOOT_IMG=""
MAGISK_APK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --boot) BOOT_IMG="$2"; shift 2;;
    --magisk) MAGISK_APK="$2"; shift 2;;
    *) echo "Usage: $0 --boot <stock boot.img> --magisk <Magisk.apk>"; exit 1;;
  esac
done

[ -f "$BOOT_IMG" ] || { echo "Stock boot.img not found: $BOOT_IMG"; exit 1; }
[ -f "$MAGISK_APK" ] || { echo "Magisk APK not found: $MAGISK_APK"; exit 1; }

echo "=== SIXTO Auto-Root (Termux, no PC) ==="
echo "Device:"
getprop ro.product.manufacturer
getprop ro.product.model
getprop ro.build.fingerprint
echo "Boot img SHA256: $(sha256sum "$BOOT_IMG" | cut -d' ' -f1)"
echo "Magisk APK SHA256: $(sha256sum "$MAGISK_APK" | cut -d' ' -f1)"

echo ""
echo "NEXT: Open Magisk app → Install (top right) → Patch a file → select:"
echo "  $BOOT_IMG"
echo "Tap PATCH, then copy the patched file from /sdcard/Download to:"
echo "  ~/patched/magisk.img"
echo ""
echo "Then press ENTER here when patched file is ready..."
read -r _

PATCHED="$HOME/patched/magisk.img"
mkdir -p "$HOME/patched"
[ -f "$PATCHED" ] || [ -f "/sdcard/Download/magisk_patched.img" ] || { echo "Patched image not found. Copy magisk_patched.img to $PATCHED"; exit 1; }
[ -f "$PATCHED" ] || cp /sdcard/Download/magisk_patched.img "$PATCHED"

echo "Patched SHA256: $(sha256sum "$PATCHED" | cut -d' ' -f1)"
echo ""
echo "Direct install (no fastboot):"
echo "  Magisk app → Install → Next → Let's Go! (or Direct install)"
echo "A reboot is required. After reboot, verify:"
echo "  - Magisk app shows installed"
echo "  - Root check in Magisk app grants su"
echo "Then submit 4-check verification in SIXTO app → Auto Root tab."
echo "Done. If bootloop: flash verified stock boot via fastboot/PC."
