"""Payment provider webhook verification.

Each provider has a distinct signature scheme in production (GCash via Xendit-type
HMAC, Maya API, card gateway). This module implements the shared pattern:

  HMAC-SHA256(secret, raw_body) == signature header  (constant-time compare)

Provider secrets come from env/secret manager. If no secret is configured,
webhooks are REJECTED (fail closed) — never auto-marked paid.

Swap in provider-specific canonicalization (sorted keys, timestamp checks)
when integrating each real gateway. The verification framework stays.
"""
import hashlib
import hmac
import os
from fastapi import HTTPException


def _secret(name: str) -> str:
    # e.g. PAY_WEBHOOK_SECRET_GCASH, PAY_WEBHOOK_SECRET_MAYA, PAY_WEBHOOK_SECRET_CARD
    return os.getenv(f"PAY_WEBHOOK_SECRET_{name.upper()}", "")


def verify_webhook_signature(provider: str, raw_body: bytes, signature: str) -> bool:
    """Constant-time HMAC verification. Empty secret → False (fail closed)."""
    secret = _secret(provider)
    if not secret:
        return False
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, (signature or "").strip().lower())


def require_verified(provider: str, raw_body: bytes, signature: str) -> None:
    if not verify_webhook_signature(provider, raw_body, signature):
        raise HTTPException(401, "Webhook signature verification failed")


def extract_provider_ref(body: dict) -> str:
    """Normalize transaction reference across providers."""
    return str(body.get("provider_ref") or body.get("transaction_id") or body.get("reference") or body.get("id") or "")


def extract_status(body: dict, paid_values: set[str] | None = None) -> str:
    paid = paid_values or {"PAID", "SUCCESS", "COMPLETED", "CAPTURED"}
    raw = (body.get("status") or body.get("state") or "").upper()
    return raw if raw else ""
