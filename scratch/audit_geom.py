#!/usr/bin/env python3
"""Check geometry column and existing location structure."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        # Sample location with geometry WKT
        r = await conn.execute(text(
            "SELECT entity_id::text, location_name, location_type, "
            "ST_AsText(geometry) as geom_wkt, uncertainty_radius_meters "
            "FROM civix.location LIMIT 3;"
        ))
        print('Sample locations with geometry:')
        for row in r.fetchall():
            m = dict(row._mapping)
            print(f"  {m['location_name']}: geom={m['geom_wkt']} type={m['location_type']}")

    async with engine.connect() as conn:
        # Check SYN locations (locations used by synthetic event_locations)
        r2 = await conn.execute(text("""
            SELECT DISTINCT l.location_name, l.location_type, ST_AsText(l.geometry) as geom
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 5
        """))
        print('Sample synthetic locations used:')
        for row in r2.fetchall():
            m = dict(row._mapping)
            print(f"  {m['location_name']} ({m['location_type']}): {m['geom']}")

    async with engine.connect() as conn:
        # Check how many distinct locations exist for synthetic cases
        r3 = await conn.execute(text("""
            SELECT COUNT(DISTINCT l.entity_id) as distinct_locations
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE c.case_number LIKE 'SYN-%'
        """))
        print(f'Distinct locations used by synthetic events: {r3.scalar()}')

    async with engine.connect() as conn:
        # Check event_location generation_run_id reference - which table stores it
        r4 = await conn.execute(text("""
            SELECT DISTINCT el.generation_run_id::text
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 3
        """))
        print('Generation run IDs used in synthetic event_locations:')
        for row in r4.fetchall():
            print(' ', row[0])

    async with engine.connect() as conn:
        # Check a specific synthetic case in detail
        r5 = await conn.execute(text("""
            SELECT c.case_id::text, c.case_number, c.title, c.case_type
            FROM civix.investigative_case c
            WHERE c.case_number = 'SYN-2025-001'
        """))
        for row in r5.fetchall():
            m = dict(row._mapping)
            print(f"Case SYN-2025-001: id={m['case_id'][:12]}... title={m['title']} type={m['case_type']}")

    async with engine.connect() as conn:
        # Case entity pool for synthetic cases
        r6 = await conn.execute(text("""
            SELECT cer.entity_id::text, e.entity_type
            FROM civix.investigative_case c
            JOIN civix.case_entity_role cer ON c.case_id = cer.case_id
            JOIN civix.entity e ON cer.entity_id = e.entity_id
            WHERE c.case_number = 'SYN-2025-001'
        """))
        print('SYN-2025-001 entities:')
        for row in r6.fetchall():
            m = dict(row._mapping)
            print(f"  entity_id={m['entity_id'][:12]}... type={m['entity_type']}")

    async with engine.connect() as conn:
        # Events for SYN-2025-001
        r7 = await conn.execute(text("""
            SELECT e.event_id::text, e.event_type, e.description, el.location_id::text
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number = 'SYN-2025-001'
            ORDER BY e.occurred_at
        """))
        print('SYN-2025-001 events:')
        for row in r7.fetchall():
            m = dict(row._mapping)
            print(f"  event_id={m['event_id'][:12]}... type={m['event_type']} loc={m['location_id'][:12]}... desc={m['description'][:50]}")

asyncio.run(main())
