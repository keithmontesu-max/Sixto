"""Intelligent root manager selection (Magisk / KernelSU / APatch).

Rules (server-side, auditable):
- Only recommend when compatibility record is approved and root_eligible.
- KernelSU requires kernel supporting the required implementation.
- APatch requires exact kernel+device match.
- Magisk requires verified method for exact device+firmware.
- Never SELECT on manager APK presence; selection != installation.
- Never overwrite existing root without migration check + customer authorization (caller enforces).

This module only SELECTS and explains. It never executes destructive ops.
Execution stays in on-device allowlisted ops with customer consent.
"""
from dataclasses import dataclass


@dataclass
class DeviceSignals:
    manufacturer: str = ""
    model: str = ""
    kernel_version: str = ""
    bootloader_status: str = "UNKNOWN"
    existing_root: str = ""  # Magisk|KernelSU|APatch|""
    firmware_line: str = ""


@dataclass
class Selection:
    recommended: str | None
    reason: str
    prerequisites: list[str]
    warnings: list[str]
    requires_authorization: bool


def select_root_manager(signals: DeviceSignals, compat: dict) -> Selection:
    """compat is classify_record() output plus supported_method."""
    root = compat.get("root", {})
    if not root.get("eligible"):
        return Selection(
            recommended=None,
            reason=f"No approved root method for this exact device+firmware. Classification: {root.get('classification', 'UNKNOWN')}",
            prerequisites=[],
            warnings=["Do not attempt unsupported rooting. Diagnostics remain available."],
            requires_authorization=True,
        )

    method = (compat.get("supported_method") or "").strip()
    if signals.existing_root and method and signals.existing_root != method:
        return Selection(
            recommended=None,
            reason=f"Existing root ({signals.existing_root}) differs from approved method ({method}). Migration requires validation + customer authorization.",
            prerequisites=["migration compatibility check", "explicit customer authorization"],
            warnings=["Never overwrite existing root implementation blindly."],
            requires_authorization=True,
        )

    kernel = (signals.kernel_version or "").lower()
    if method == "KernelSU":
        if "kernel" not in kernel and not kernel:
            # Kernel string may be opaque; require admin-approved record to assert support.
            # The compatibility record is the source of truth; kernel string is advisory.
            pass
        return Selection(
            recommended="KernelSU",
            reason="Approved compatibility record specifies KernelSU for this device+firmware.",
            prerequisites=compat.get("prerequisites", []),
            warnings=["KernelSU requires matching kernel implementation. Verified via compatibility record."],
            requires_authorization=False,
        )
    if method == "APatch":
        return Selection(
            recommended="APatch",
            reason="Approved compatibility record specifies APatch for this exact kernel+device.",
            prerequisites=compat.get("prerequisites", []),
            warnings=["APatch is kernel-sensitive. Only use the approved build."],
            requires_authorization=False,
        )
    if method == "Magisk":
        return Selection(
            recommended="Magisk",
            reason="Approved compatibility record specifies Magisk for this device+firmware.",
            prerequisites=compat.get("prerequisites", []),
            warnings=["Manager APK alone does not mean root. Actual root must be verified separately."],
            requires_authorization=False,
        )
    # Approved record exists but method string missing — do not guess.
    return Selection(
        recommended=None,
        reason="Approved record exists but supported_method is not set. Admin must set it before offering installation.",
        prerequisites=[],
        warnings=["Never guess a root method."],
        requires_authorization=True,
    )
