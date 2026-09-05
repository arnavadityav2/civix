#!/usr/bin/env python3
"""Get remaining enum and schema info for remediation."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        r1 = await conn.execute(text("SELECT DISTINCT location_predicate FROM civix.event_location LIMIT 10;"))
        print('Location predicates:')
        for row in r1.fetchall():
            print(' ', row[0])
        
        r2 = await conn.execute(text("SELECT DISTINCT epistemic_status FROM civix.event_location LIMIT 10;"))
        print('Epistemic statuses:')
        for row in r2.fetchall():
            print(' ', row[0])
        
        r3 = await conn.execute(text("SELECT DISTINCT role FROM civix.case_entity_role LIMIT 20;"))
        print('Entity roles:')
        for row in r3.fetchall():
            print(' ', row[0])
        
        r4 = await conn.execute(text("SELECT generation_run_id::text, run_label, created_at FROM civix.generation_run ORDER BY created_at DESC LIMIT 3;"))
        print('Generation runs:')
        for row in r4.fetchall():
            print(' ', dict(row._mapping))
        
        r5 = await conn.execute(text("SELECT * FROM civix.location LIMIT 1;"))
        print('Sample location:')
        for row in r5.fetchall():
            m = dict(row._mapping)
            for k, v in m.items():
                print(f'  {k}: {v}')
        
        # Get events with location_predicate being 'LOCATED_AT'
        r6 = await conn.execute(text("""
            SELECT e.event_type, LEFT(e.description, 60) as desc_preview
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 5
        """))
        print('Sample synthetic events:')
        for row in r6.fetchall():
            m = dict(row._mapping)
            print(f"  type={m['event_type']} desc={m['desc_preview']}")

        # Synthetic cases with > 1 distinct location
        r7 = await conn.execute(text("""
            SELECT el.case_id::text, COUNT(DISTINCT el.location_id) as distinct_locs, COUNT(el.event_id) as event_count
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            GROUP BY el.case_id
            ORDER BY distinct_locs DESC
            LIMIT 5
        """))
        print('Synthetic cases with most distinct locations:')
        for row in r7.fetchall():
            m = dict(row._mapping)
            print(f"  case_id={m['case_id'][:12]}... locs={m['distinct_locs']} events={m['event_count']}")

        # How many cases have all events at same location
        r8 = await conn.execute(text("""
            SELECT COUNT(*) as static_cases FROM (
                SELECT el.case_id, COUNT(DISTINCT el.location_id) as distinct_locs
                FROM civix.event_location el
                JOIN civix.investigative_case c ON el.case_id = c.case_id
                WHERE c.case_number LIKE 'SYN-%'
                GROUP BY el.case_id
                HAVING COUNT(DISTINCT el.location_id) <= 1
            ) sub
        """))
        print(f'Synthetic cases with only 1 or fewer distinct locations: {r8.scalar()}')

asyncio.run(main())
