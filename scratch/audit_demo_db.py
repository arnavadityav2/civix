"""
CIVIX Phase 2 DB Audit - using actual .env credentials
"""
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# From .env file
DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

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
        # Basic counts
        res = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_case"))
        report['total_cases'] = res.scalar()
        res = await conn.execute(text("SELECT COUNT(*) FROM civix.person"))
        report['total_persons'] = res.scalar()
        res = await conn.execute(text("SELECT COUNT(*) FROM civix.case_entity_role"))
        report['total_case_entity_roles'] = res.scalar()

        # Person columns
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'civix' AND table_name = 'person' ORDER BY ordinal_position"
        ))
        report['person_columns'] = [r[0] for r in res.fetchall()]

        # Check for avatar_url  
        report['has_avatar_url'] = 'avatar_url' in report['person_columns']

        # Sample cases
        res = await conn.execute(text(
            "SELECT case_number, title, status FROM civix.investigative_case ORDER BY case_number LIMIT 20"
        ))
        report['sample_cases'] = [{"number": r[0], "title": r[1], "status": r[2]} for r in res.fetchall()]

        # Indexed persons in DB
        ids_str = ",".join(f"'{p}'" for p in INDEXED_PERSON_IDS)
        res = await conn.execute(text(
            f"SELECT entity_id::text, display_name FROM civix.person WHERE entity_id = ANY(ARRAY[{ids_str}]::uuid[])"
        ))
        report['indexed_persons_in_db'] = [{"id": r[0], "name": r[1]} for r in res.fetchall()]

        # Case-entity roles for indexed persons
        if report['indexed_persons_in_db']:
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

        # Golden case check
        res = await conn.execute(text(
            """SELECT c.case_id::text, c.case_number, c.title, c.status 
               FROM civix.investigative_case c WHERE c.case_number = 'CIV-2012-001'"""
        ))
        row = res.fetchone()
        report['golden_case_civ2012001'] = {"id": row[0], "number": row[1], "title": row[2], "status": row[3]} if row else None

        # CCTV observation table details
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'civix' AND table_name = 'cctv_observation' ORDER BY ordinal_position"
        ))
        report['cctv_observation_columns'] = [r[0] for r in res.fetchall()]

        # CCTV observations count
        try:
            res = await conn.execute(text("SELECT COUNT(*) FROM civix.cctv_observation"))
            report['cctv_observation_count'] = res.scalar()
        except Exception as e:
            report['cctv_observation_count'] = f"ERROR: {e}"

        # CCTV cameras count
        try:
            res = await conn.execute(text("SELECT COUNT(*) FROM civix.cctv_camera"))
            report['cctv_camera_count'] = res.scalar()
            res = await conn.execute(text("SELECT camera_code, display_name, city, region FROM civix.cctv_camera LIMIT 5"))
            report['sample_cameras'] = [{"code": r[0], "name": r[1], "city": r[2], "region": r[3]} for r in res.fetchall()]
        except Exception as e:
            report['cctv_camera_count'] = f"ERROR: {e}"

        # All tables
        res = await conn.execute(text(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix' ORDER BY table_name"
        ))
        report['all_civix_tables'] = [r[0] for r in res.fetchall()]

        # Check location table
        res = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = 'civix' AND table_name = 'location' ORDER BY ordinal_position"
        ))
        report['location_columns'] = [r[0] for r in res.fetchall()]

        # Check event_location table
        try:
            res = await conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'civix' AND table_name = 'event_location' ORDER BY ordinal_position"
            ))
            report['event_location_columns'] = [r[0] for r in res.fetchall()]
        except:
            report['event_location_columns'] = "TABLE NOT FOUND"

    print(json.dumps(report, indent=2, default=str))
    with open("scratch/audit_demo_db.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print("\nSaved to scratch/audit_demo_db.json")

if __name__ == "__main__":
    asyncio.run(main())
