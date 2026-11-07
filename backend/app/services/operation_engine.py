"""Automated Root Command Engine — orchestration, never execution of arbitrary commands.

Flow: DEVICE DETECTION → COMPATIBILITY → METHOD SELECTION → WORKFLOW GENERATION
      → PRE-EXECUTION VALIDATION → CUSTOMER APPROVAL → AUTHORIZED LOCAL EXECUTION
      → RESULT VERIFICATION → OPERATION REPORT

Security: typed allowlisted ops only (adapter steps). Each op has id, timeout,
expected result, verification, failure handling. Destructive steps never run
without `authorized_by_customer=True` on the operation record.
"""
from app.services.adapters.registry import get_adapter, list_methods


def plan_operation(method: str, compat: dict) -> dict:
    """Generate a workflow plan. Returns {ok, ...}. Never plans when ineligible.

    Method BOOTLOADER_UNLOCK plans from the bootloader verdict, not root.
    Never FRP/account-lock bypass — requires OEM + manufacturer auth where applicable.
    """
    name = (method or compat.get("supported_method") or "").strip()
    spec = get_adapter(name)
    if spec is None:
        return {"ok": False, "reason": f"No approved adapter for method '{name}'.", "steps": [], "prerequisites": [], "recovery": []}
    if spec.method == "BOOTLOADER_UNLOCK":
        boot = compat.get("bootloader", {})
        if not boot.get("eligible"):
            return {"ok": False,
                    "reason": f"Bootloader not eligible ({boot.get('classification', 'UNKNOWN')}). No operations planned.",
                    "steps": [], "prerequisites": [], "recovery": []}
    else:
        root = compat.get("root", {})
        if not root.get("eligible"):
            return {"ok": False,
                    "reason": f"Root not eligible ({root.get('classification', 'UNKNOWN')}). No operations planned.",
                    "steps": [], "prerequisites": [], "recovery": []}
    return {"ok": True, "method": spec.method,
            "prerequisites": spec.prerequisites, "steps": spec.to_dict()["steps"],
            "recovery": spec.recovery, "verification_checks": spec.verification_checks,
            "requires_authorization": any(s.destructive for s in spec.steps)}


def verify_bootloader(report: dict) -> dict:
    """3-step bootloader verification. Never on exit code alone."""
    checks = {
        "bootloader_unlocked": bool(report.get("bootloader_unlocked")),
        "wipe_acknowledged": bool(report.get("wipe_acknowledged")),
        "authorization_completed": bool(report.get("authorization_completed")),
    }
    passed = sum(checks.values())
    success = passed == 3
    failed = [k for k, v in checks.items() if not v]
    return {"success": success, "checks": checks, "failed": failed,
            "verdict": "BOOTLOADER VERIFIED" if success else f"BOOTLOADER NOT VERIFIED ({passed}/3)"}


def verify_operation(report: dict) -> dict:
    """4-step root verification. Never reports success on install exit code alone.

    report fields (from on-device checks):
      implementation_installed: bool
      kernel_boot_compatible: bool
      manager_installed: bool
      actual_root_available: bool
    All four must be True for ROOT SUCCESSFUL.
    """
    checks = {
        "implementation_installed": bool(report.get("implementation_installed")),
        "kernel_boot_compatible": bool(report.get("kernel_boot_compatible")),
        "manager_installed": bool(report.get("manager_installed")),
        "actual_root_available": bool(report.get("actual_root_available")),
    }
    passed = sum(checks.values())
    success = passed == 4
    failed = [k for k, v in checks.items() if not v]
    return {"success": success, "checks": checks, "failed": failed,
            "verdict": "ROOT VERIFIED" if success else f"ROOT NOT VERIFIED ({passed}/4 checks passed)"}


def available_methods() -> list[str]:
    return list_methods()
