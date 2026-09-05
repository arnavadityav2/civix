#!/usr/bin/env python3
"""Get final remaining schema info."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        # Location predicates used
        r1 = await conn.execute(text("SELECT DISTINCT location_predicate FROM civix.event_location LIMIT 10;"))
        print('Location predicates:')
        for row in r1.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        r2 = await conn.execute(text("SELECT DISTINCT epistemic_status FROM civix.event_location LIMIT 10;"))
        print('Epistemic statuses (event_location):')
        for row in r2.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        r3 = await conn.execute(text("SELECT DISTINCT role FROM civix.case_entity_role LIMIT 20;"))
        print('Entity roles:')
        for row in r3.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        # generation_run schema
        r4 = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='generation_run' ORDER BY ordinal_position;"
        ))
        print('generation_run columns:')
        for row in r4.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']})")

    async with engine.connect() as conn:
        try:
            r5 = await conn.execute(text("SELECT * FROM civix.generation_run LIMIT 2;"))
            print('Sample generation_run:')
            for row in r5.fetchall():
                m = dict(row._mapping)
                for k, v in m.items():
                    print(f'  {k}: {v}')
        except Exception as e:
            print(f'generation_run error: {e}')

    async with engine.connect() as conn:
        # Sample location
        r6 = await conn.execute(text("SELECT entity_id::text, location_name, location_type FROM civix.location LIMIT 3;"))
        print('Sample locations:')
        for row in r6.fetchall():
            m = dict(row._mapping)
            print(f"  {m['location_name']} (type={m['location_type']})")

    async with engine.connect() as conn:
        # Sample synthetic events (description quality)
        r7 = await conn.execute(text("""
            SELECT e.event_type, LEFT(e.description, 80) as desc_preview, e.occurred_at
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 5
        """))
        print('Sample synthetic events:')
        for row in r7.fetchall():
            m = dict(row._mapping)
            print(f"  type={m['event_type']} desc={m['desc_preview']}")

    async with engine.connect() as conn:
        # Static vs dynamic location coverage
        r8 = await conn.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE distinct_locs <= 1) as static_cases,
                COUNT(*) FILTER (WHERE distinct_locs > 1) as dynamic_cases
            FROM (
                SELECT el.case_id, COUNT(DISTINCT el.location_id) as distinct_locs
                FROM civix.event_location el
                JOIN civix.investigative_case c ON el.case_id = c.case_id
                WHERE c.case_number LIKE 'SYN-%'
                GROUP BY el.case_id
            ) sub
        """))
        row = r8.fetchone()
        m = dict(row._mapping)
        print(f'Static cases (1 loc): {m["static_cases"]}, Dynamic cases (>1 loc): {m["dynamic_cases"]}')

asyncio.run(main())
