"""Compatibility seed — scaffold only. Records are UNKNOWN/unapproved until
a technician tests on real hardware and an admin approves them.

Never fabricate rootability. Every manufacturer starts UNKNOWN.
Vivo is EXCLUDED from Auto Root catalog (business policy).
"""
import asyncio
from sqlalchemy import select
from app.database import async_session, engine
from app.models import CompatibilityRecord

VENDORS = [
    ("samsung", "Galaxy UNKNOWN"),
    ("Xiaomi", "UNKNOWN"), ("Redmi", "UNKNOWN"), ("POCO", "UNKNOWN"),
    ("Infinix", "UNKNOWN"), ("TECNO", "UNKNOWN"),
    ("Google", "Pixel UNKNOWN"), ("Motorola", "UNKNOWN"),
    ("OnePlus", "UNKNOWN"), ("Realme", "UNKNOWN"), ("OPPO", "UNKNOWN"),
    ("ASUS", "UNKNOWN"), ("Nothing", "UNKNOWN"), ("Sony", "UNKNOWN"),
    ("Nokia", "UNKNOWN"),
]

# Example approved records must be added manually after real-device testing.
# The Vivo exclusion is the only seeded exclusion; everything else is UNKNOWN.


async def main():
    async with async_session() as db:
        for mfr, model in VENDORS:
            ex = await db.execute(select(CompatibilityRecord).where(
                CompatibilityRecord.manufacturer.ilike(mfr), CompatibilityRecord.model.ilike(model)))
            if not ex.scalar_one_or_none():
                db.add(CompatibilityRecord(
                    manufacturer=mfr, model=model,
                    root_classification="UNKNOWN", bootloader_classification="UNKNOWN",
                    root_eligible=False, unlock_eligible=False, is_approved=False,
                ))
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
        await db.commit()
        print(f"Seeded {len(VENDORS)+1} compatibility scaffolds (all UNKNOWN until tested)")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
