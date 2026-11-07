"""Adapter registry — only admin-approved methods are instantiable.
New methods require OWNER approval + security review before registration.

Includes root adapters (Magisk/KernelSU/APatch) + legitimate bootloader
unlock adapter (owner consent, never FRP/account-lock bypass).
"""
from app.services.adapters import magisk, kernelsu, apatch, bootloader

REGISTRY = {
    "Magisk": magisk.SPEC,
    "KernelSU": kernelsu.SPEC,
    "APatch": apatch.SPEC,
    "BOOTLOADER_UNLOCK": bootloader.SPEC,
}


def get_adapter(method: str):
    return REGISTRY.get((method or "").strip())


def list_methods() -> list[str]:
    return sorted(REGISTRY.keys())
