"""
CIVIX Biometric Full Audit Script
Run this to gather ground-truth data for the audit.
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

INDEXED_PERSON_IDS = [
    'f5c4a848-1c97-4b39-cc96-bb0b4775f8e3',
    '637038f4-633f-8457-6de9-b7142bc10381',
    '7bfb4b76-8bee-ccaf-10a6-009a09e6fc04',
    '52cc467a-a55d-bbcb-fde9-985e251570de',
    'd5104adc-27e6-2c80-0166-c8d673715d46',
    '263f32c4-30fd-40a8-b01b-6def1b47e90c',
    '09d7a50a-82dd-4acf-1c8c-ed1d70f5b332',
    'd747317f-ea1d-8e98-bc65-6f29f10d54f9',
    '2e13da11-9613-34c3-cff3-6fdcc99038ee',
    '4b2aa1e0-3847-82ce-663d-dba144184ab6',
]

async def main():
    engine = create_async_engine(DB_URL)
    report = {}

    async with engine.connect() as conn:
        # 1. Person table columns
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'civix' AND table_name = 'person' ORDER BY ordinal_position"
        ))
        report['person_columns'] = [r[0] for r in res.fetchall()]

        # 2. Indexed persons in DB
        ids_str = ",".join(f"'{p}'" for p in INDEXED_PERSON_IDS)
        res = await conn.execute(text(
            f"SELECT entity_id::text, display_name FROM civix.person WHERE entity_id = ANY(ARRAY[{ids_str}]::uuid[])"
        ))
        report['indexed_persons_in_db'] = [{"id": r[0], "name": r[1]} for r in res.fetchall()]

        # 3. Case-Entity roles for indexed persons
        res = await conn.execute(text(
            f"""SELECT p.entity_id::text, p.display_name, cer.role::text, c.case_number, c.title 
                FROM civix.person p
                JOIN civix.case_entity_role cer ON p.entity_id = cer.entity_id
                JOIN civix.investigative_case c ON cer.case_id = c.case_id
                WHERE p.entity_id = ANY(ARRAY[{ids_str}]::uuid[])
                ORDER BY p.display_name"""
        ))
        report['indexed_persons_case_roles'] = [
            {"person_id": r[0], "name": r[1], "role": r[2], "case_number": r[3], "case_title": r[4]}
            for r in res.fetchall()
        ]

        # 4. Total cases
        res = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_case"))
        report['total_cases'] = res.scalar()

        # 5. Total persons
        res = await conn.execute(text("SELECT COUNT(*) FROM civix.person"))
        report['total_persons'] = res.scalar()

        # 6. Persons with PERSON entity type in any case
        res = await conn.execute(text(
            """SELECT COUNT(DISTINCT p.entity_id) FROM civix.person p
               JOIN civix.entity e ON p.entity_id = e.entity_id
               JOIN civix.case_entity_role cer ON p.entity_id = cer.entity_id"""
        ))
        report['persons_linked_to_cases'] = res.scalar()

        # 7. Check if avatar_url column exists in person table
        report['has_avatar_url'] = 'avatar_url' in report['person_columns']

        # 8. Golden case - CIV-2012-001
        res = await conn.execute(text(
            """SELECT c.case_id::text, c.case_number, c.title, c.status, COUNT(DISTINCT cer.entity_id) as entities
               FROM civix.investigative_case c
               LEFT JOIN civix.case_entity_role cer ON c.case_id = cer.case_id
               WHERE c.case_number = 'CIV-2012-001'
               GROUP BY c.case_id, c.case_number, c.title, c.status"""
        ))
        row = res.fetchone()
        report['golden_case_civ2012001'] = {"id": row[0], "number": row[1], "title": row[2], "status": row[3], "entities": row[4]} if row else None

        # 9. CCTV observations table check
        res = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix' AND table_name LIKE 'cctv%'"
        ))
        report['cctv_tables'] = [r[0] for r in res.fetchall()]

        # 10. Check biometric-related tables
        res = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix' ORDER BY table_name"
        ))
        report['all_civix_tables'] = [r[0] for r in res.fetchall()]

    print(json.dumps(report, indent=2, default=str))
    with open("scratch/audit_biometric_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print("\nReport saved to scratch/audit_biometric_report.json")

if __name__ == "__main__":
    asyncio.run(main())
