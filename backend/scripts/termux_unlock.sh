#!/system/bin/sh
# SIXTO Termux OTG Unlock — runs on YOUR ROOTED phone (host) to unlock CUSTOMER phone (target) via USB OTG.
#
# Setup (host, once):
#   pkg install -y root-repo
#   pkg install -y fastboot-android adb
#   # verify: fastboot --version
#
# Run (host, per customer):
#   su -c "sh termux_unlock.sh"
#
# Steps (all supervised, never blind):
#   1. adb devices (customer must tap "Allow USB debugging" on THEIR phone)
#   2. adb reboot bootloader (customer phone → fastboot)
#   3. fastboot devices (OTG must show customer serial)
#   4. fastboot getvar unlocked (must be "no" before, "yes" after)
#   5. fastboot flashing unlock (WARNING: wipes customer data — they must confirm)
#   6. customer taps Volume+ UP on their phone (required by Google fastboot)
#   7. fastboot getvar unlocked again → verify yes
#   8. fastboot reboot
#
# Safety:
# - Customer phone must be THEIR device with consent. The host never touches another person's lock state without them.
# - NEVER FRP/account-lock bypass: flashing unlock does not bypass FRP. If FRP prompt appears, stop.
# - Wrong timing = retry prompt (!). Read the fastboot screen on customer phone.
#
set -e
echo "=== SIXTO OTG Unlock (host=your rooted phone, target=customer phone) ==="
echo "Plug customer phone via USB OTG to THIS phone."
echo "On customer phone: Enable USB debugging (Settings → Developer) if shown."
echo ""
printf "Customer consents to UNLOCK + DATA WIPE? Type CUSTOMER YES to continue: "
read _ yn
[ "$yn" = "CUSTOMER YES" ] || { echo "Cancelled — no consent, no unlock."; exit 0; }

echo "[1] adb devices"
adb devices
echo ""
echo "Check customer serial is 'device'. Press ENTER to continue (or Ctrl+C)..."
read _

echo "[2] adb reboot bootloader"
adb reboot bootloader
sleep 5

echo "[3] fastboot devices"
fastboot devices

echo "[4] fastboot getvar unlocked"
fastboot getvar unlocked

echo "[5] fastboot flashing unlock"
echo "On CUSTOMER phone now: press Volume UP to confirm unlock."
fastboot flashing unlock

echo "[6] fastboot getvar unlocked (verify)"
fastboot getvar unlocked

echo "[7] fastboot reboot"
fastboot reboot

echo "Done. Customer phone wipes + reboots. Verify unlocked=yes, then root via Auto Root."
