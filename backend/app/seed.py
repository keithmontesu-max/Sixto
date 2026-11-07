"""Seed bootstrap — creates first OWNER + sample catalog. Run once:
python -m app.seed
Env: OWNER_EMAIL, OWNER_PASSWORD, OWNER_NAME"""
import asyncio
import os
from sqlalchemy import select
from app.database import async_session, engine
from app.models import User, Role, CompatibilityRecord, Service
from app.security import hash_password


async def main():
    async with async_session() as db:
        owner_email = os.getenv("OWNER_EMAIL", "owner@sixto.example.com")
        existing = await db.execute(select(User).where(User.email == owner_email))
        if not existing.scalar_one_or_none():
            owner = User(
                email=owner_email,
                password_hash=hash_password(os.getenv("OWNER_PASSWORD", "ChangeMe123!AtFirstLogin")),
                role=Role.OWNER.value,
                full_name=os.getenv("OWNER_NAME", "SIXTO Owner"),
                is_active=True,
                is_verified=True,
            )
            db.add(owner)
            print(f"OWNER created: {owner_email}")
        # Service catalog seed (prices are placeholders — admin edits in dashboard)
        for name, slug, price in [
            ("Auto Root Service (Supported Devices)", "auto-root", 149900),
            ("Bootloader Unlock Assistance", "bootloader-unlock", 99900),
            ("Root Verification", "root-verification", 24900),
            ("Device Diagnostics", "diagnostics", 19900),
            ("Root Troubleshooting", "troubleshooting", 34900),
            ("Remote Technical Assistance", "remote-assist", 49900),
        ]:
            ex = await db.execute(select(Service).where(Service.slug == slug))
            if not ex.scalar_one_or_none():
                db.add(Service(name=name, slug=slug, description=name,
                               price_cents=price, currency="PHP", eta_minutes=60,
                               refund_policy="Refund per Terms of Service"))
        # Vivo exclusion example (business policy, not technical claim)
        ex2 = await db.execute(select(CompatibilityRecord).where(
            CompatibilityRecord.manufacturer.ilike("vivo")))
        if not ex2.scalar_one_or_none():
            db.add(CompatibilityRecord(
                manufacturer="vivo", model="Policy Exclusion", model_id="*",
                root_classification="EXCLUDED", bootloader_classification="UNKNOWN",
                root_eligible=False, unlock_eligible=False,
                is_approved=True, is_excluded=True,
                exclusion_reason="EXCLUDED from initial Auto Root catalog (business policy)",
            ))
        # Demo payment_methods (one-click local). Real owners overwrite in Admin → Business Config.
        from app.models import BusinessConfig
        pm = await db.execute(select(BusinessConfig).where(BusinessConfig.key == "payment_methods"))
        if not pm.scalar_one_or_none():
            db.add(BusinessConfig(key="payment_methods", value={
                "gcash_number": os.getenv("PAY_GCASH", "09XXXXXXXXXX"),
                "gcash_name": os.getenv("PAY_NAME", "SIXTO Owner"),
                "maya_number": os.getenv("PAY_MAYA", "09XXXXXXXXXX"),
                "maya_name": os.getenv("PAY_NAME", "SIXTO Owner"),
                "instructions": "Pay the owner directly, then submit your transaction reference in My Orders → detail.",
            }))
        await db.commit()
        print("Seed complete")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
