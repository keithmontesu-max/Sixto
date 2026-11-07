from app.services.adapters.base import AdapterSpec, OpStep

SPEC = AdapterSpec(
    method="Magisk",
    prerequisites=[
        "Bootloader unlocked (or unlockable via approved workflow)",
        "Data backup acknowledged by customer (unlock erases data)",
        "Device matched to an approved compatibility record",
        "No existing root implementation conflict (or migration approved)",
    ],
    steps=[
        OpStep("detect", "Detect device + verify compatibility record is approved", expected_result="compat approved", verification="server lookup returns eligible=true"),
        OpStep("patch_boot", "Prepare patched boot image via supported local interface", destructive=True, expected_result="patched image ready", verification="patcher exits 0 AND image hash recorded", timeout_seconds=180),
        OpStep("flash", "Flash patched boot image via supported local interface (fastboot when required)", destructive=True, expected_result="flash completed", verification="boot clears + kernel intact", timeout_seconds=180),
        OpStep("install_manager", "Install Magisk manager package", expected_result="manager installed", verification="PackageManager reports installed"),
    ],
    recovery=[
        "Hold power+volume per device to boot recovery; reflash stock boot image for this build.",
        "Never retry flash after timeout without checking device state first.",
        "If bootloop: flash verified stock boot image for the exact build fingerprint.",
    ],
    verification_checks=[
        "Root implementation installed (manager reports installed)",
        "Kernel/boot image compatibility (boot image matches device build)",
        "Manager application installed (PackageManager)",
        "Actual root availability (su access check on-device, supervised)",
    ],
)
