#!/usr/bin/env python3
"""Check analysis_run and investigative_lead FK constraints."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        r = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='analysis_run' ORDER BY ordinal_position;"
        ))
        print('analysis_run columns:')
        for row in r.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']})")

    async with engine.connect() as conn:
        try:
            r2 = await conn.execute(text("SELECT run_id::text, run_label FROM civix.analysis_run LIMIT 3;"))
            print('Sample analysis_run:')
            for row in r2.fetchall():
                print(' ', dict(row._mapping))
        except Exception as e:
            print(f'analysis_run error: {e}')

    async with engine.connect() as conn:
        # Check what person_id to use for generated_by_person
        r3 = await conn.execute(text(
            "SELECT entity_id::text, display_name FROM civix.person "
            "WHERE display_name LIKE '%System%' OR display_name LIKE '%Admin%' OR display_name LIKE '%CIVIX%' "
            "LIMIT 3;"
        ))
        print('System persons:')
        for row in r3.fetchall():
            print(' ', dict(row._mapping))

    async with engine.connect() as conn:
        # Check if the 00000000...1 UUID exists as a person
        r4 = await conn.execute(text(
            "SELECT entity_id::text, display_name FROM civix.person WHERE entity_id = '00000000-0000-0000-0000-000000000001'::uuid;"
        ))
        result = r4.fetchone()
        if result:
            print(f'System user found: {dict(result._mapping)}')
        else:
            print('System user 00000000-...1 not found in person table')

    async with engine.connect() as conn:
        # Check the constraint in investigative_lead for generated_by_run_id
        r5 = await conn.execute(text("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_schema = 'civix' AND table_name = 'investigative_lead'
        """))
        print('investigative_lead constraints:')
        for row in r5.fetchall():
            print(' ', dict(row._mapping))

asyncio.run(main())
