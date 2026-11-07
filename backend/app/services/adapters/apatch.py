from app.services.adapters.base import AdapterSpec, OpStep

SPEC = AdapterSpec(
    method="APatch",
    prerequisites=[
        "Exact kernel + device satisfy APatch requirements (compatibility record)",
        "Bootloader state compatible with approved route",
    ],
    steps=[
        OpStep("kernel_check", "Verify exact kernel + device match APatch requirements", expected_result="match confirmed", verification="kernel/device match approved record"),
        OpStep("install", "Install APatch implementation via supported local interface", destructive=True, expected_result="implementation installed", verification="on-device check reports implementation present", timeout_seconds=180),
        OpStep("install_manager", "Install APatch manager package", expected_result="manager installed", verification="PackageManager reports installed"),
    ],
    recovery=[
        "Restore stock boot image for the exact build if boot fails.",
        "APatch is kernel-sensitive — stock image must match the exact build fingerprint.",
    ],
    verification_checks=[
        "Root implementation installed",
        "Kernel/boot image compatibility",
        "Manager application installed",
        "Actual root availability (supervised su check)",
    ],
)
