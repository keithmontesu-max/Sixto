from app.services.adapters.base import AdapterSpec, OpStep

SPEC = AdapterSpec(
    method="KernelSU",
    prerequisites=[
        "Kernel supports the required KernelSU implementation (verified via compatibility record)",
        "Bootloader state compatible with the approved installation route",
        "Device matched to an approved record (never guess kernel support)",
    ],
    steps=[
        OpStep("kernel_check", "Verify kernel supports required KernelSU implementation", expected_result="kernel supported", verification="kernel version matches approved range"),
        OpStep("install", "Install KernelSU implementation via supported local interface", destructive=True, expected_result="implementation installed", verification="on-device check reports implementation present", timeout_seconds=180),
        OpStep("install_manager", "Install KernelSU manager package", expected_result="manager installed", verification="PackageManager reports installed"),
    ],
    recovery=[
        "Restore stock kernel/boot for the exact firmware if boot fails.",
        "Do not downgrade KernelSU manager without checking kernel compatibility.",
    ],
    verification_checks=[
        "Root implementation installed",
        "Kernel/boot image compatibility",
        "Manager application installed",
        "Actual root availability (supervised su check)",
    ],
)
