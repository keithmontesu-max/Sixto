from app.services.adapters.base import AdapterSpec, OpStep

SPEC = AdapterSpec(
    method="BOOTLOADER_UNLOCK",
    prerequisites=[
        "OEM unlocking enabled on-device (Settings → Developer options)",
        "Data backup acknowledged — unlocking erases user data",
        "Device matched to approved bootloader record",
        "Manufacturer account authorization completed where required (e.g. Mi Unlock token)",
    ],
    steps=[
        OpStep("oem_check", "Verify OEM unlocking toggle is enabled on-device", expected_result="enabled", verification="settings state reported by device"),
        OpStep("reboot_fastboot", "Reboot to fastboot/bootloader mode", expected_result="fastboot ready", verification="fastboot getvar unlocked = no (before)"),
        OpStep("unlock", "Flashing unlock via vendor fastboot interface (Pixel/generic) or manufacturer tool (Xiaomi Mi Unlock)", destructive=True, expected_result="unlock accepted", verification="fastboot getvar unlocked = yes (after)", timeout_seconds=240),
        OpStep("boot_verify", "Boot back to system and verify unlock state", expected_result="unlocked=true", verification="verifiedbootstate=orange + flash.locked=0"),
    ],
    recovery=[
        "If fastboot not detected: reinstall USB drivers, use original cable, toggle USB debugging.",
        "If Xiaomi: complete Mi Unlock token wait (7–15 days typical) — server cannot skip this.",
        "Never flash a boot image for a different build fingerprint.",
    ],
    verification_checks=[
        "Bootloader unlocked reported by device",
        "Data-wipe acknowledged by customer",
        "Manufacturer authorization completed (where applicable)",
    ],
)
