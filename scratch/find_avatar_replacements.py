"""
Find replacement persons with avatars for the biometric cohort.
Run this when some cohort members lack avatar images.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text
from civix_api.config import settings

COHORT_PATH = Path(__file__).resolve().parent / "biometric_demo_cohort.json"

async def find_replacements():
    with open(COHORT_PATH) as f:
        cohort = json.load(f)

    current_ids = {
        p["entity_id"] for p in
        cohort["investigative_subjects"] + cohort["civilians"]
    }

    engine = create_async_engine(settings.civix_database_url, echo=False)
    async with AsyncSession(engine) as session:
        r = await session.execute(text("""
            SELECT DISTINCT p.entity_id::text, p.display_name, p.avatar_url,
                cer.role::text AS primary_role,
                COUNT(DISTINCT cer.case_id) AS case_count,
                MAX(CASE WHEN ic.case_number NOT LIKE 'SYN-%' THEN 1 ELSE 0 END) AS is_hero,
                CASE
                    WHEN EXISTS (
                        SELECT 1 FROM civix.case_entity_role cer2
                        WHERE cer2.entity_id = p.entity_id
                          AND cer2.role::text IN ('SUSPECT','ACCUSED','PERSON_OF_INTEREST')
                    ) THEN 'INVESTIGATIVE_SUBJECT'
                    ELSE 'CIVILIAN'
                END AS classification
            FROM civix.person p
            JOIN civix.case_entity_role cer ON p.entity_id = cer.entity_id
            JOIN civix.investigative_case ic ON cer.case_id = ic.case_id
            WHERE p.avatar_url IS NOT NULL
              AND cer.role::text IN ('SUSPECT','ACCUSED','PERSON_OF_INTEREST',
                                     'VICTIM','COMPLAINANT','WITNESS','INFORMANT','RELATED_PERSON')
            GROUP BY p.entity_id, p.display_name, p.avatar_url, cer.role
            ORDER BY is_hero DESC, case_count DESC
        """))
        rows = [dict(r._mapping) for r in r.fetchall()]

    await engine.dispose()

    subjects = [r for r in rows if r["classification"] == "INVESTIGATIVE_SUBJECT" and r["entity_id"] not in current_ids]
    civilians = [r for r in rows if r["classification"] == "CIVILIAN" and r["entity_id"] not in current_ids]

    print("Available replacement INVESTIGATIVE SUBJECTS (with avatars):")
    for p in subjects[:10]:
        hero = "[HERO]" if p["is_hero"] else "[SYN]"
        name = p["display_name"]
        eid = p["entity_id"][:8]
        role = p["primary_role"]
        cases = p["case_count"]
        print(f"  {hero} {name} ({eid}) role={role} cases={cases}")

    print("\nAvailable replacement CIVILIANS (with avatars):")
    for p in civilians[:10]:
        hero = "[HERO]" if p["is_hero"] else "[SYN]"
        name = p["display_name"]
        eid = p["entity_id"][:8]
        role = p["primary_role"]
        cases = p["case_count"]
        print(f"  {hero} {name} ({eid}) role={role} cases={cases}")

    return subjects, civilians

asyncio.run(find_replacements())
