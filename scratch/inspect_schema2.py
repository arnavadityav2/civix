#!/usr/bin/env python3
"""Inspect full schema relationships relevant to investigative semantics remediation."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

TABLES = [
    'event', 'event_location', 'event_participant', 'investigative_lead',
    'source_record', 'fir', 'assertion', 'case_entity_role',
    'investigative_case', 'entity', 'person', 'organization'
]

async def main():
    async with engine.connect() as conn:
        for tbl in TABLES:
            r = await conn.execute(text(
                f"SELECT column_name, data_type "
                f"FROM information_schema.columns "
                f"WHERE table_schema='civix' AND table_name='{tbl}' "
                f"ORDER BY ordinal_position;"
            ))
            rows = r.fetchall()
            if rows:
                print(f'\n=== {tbl.upper()} ===')
                for row in rows:
                    m = dict(row._mapping)
                    print(f"  {m['column_name']} ({m['data_type']})")
            else:
                print(f'\n=== {tbl.upper()} *** DOES NOT EXIST ***')

        # How are events linked to cases?
        print('\n\n=== CHECKING EVENT→CASE LINK TABLES ===')
        # Check for any table with both event_id and case_id
        r2 = await conn.execute(text("""
            SELECT table_name FROM information_schema.columns
            WHERE table_schema='civix' AND column_name='event_id'
            GROUP BY table_name ORDER BY table_name;
        """))
        print("Tables with event_id:", [row[0] for row in r2.fetchall()])

        r3 = await conn.execute(text("""
            SELECT table_name FROM information_schema.columns
            WHERE table_schema='civix' AND column_name='case_id'
            GROUP BY table_name ORDER BY table_name;
        """))
        print("Tables with case_id:", [row[0] for row in r3.fetchall()])

        # Check investigative_lead count
        try:
            r4 = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_lead;"))
            print(f"\nInvestigative Lead count: {r4.scalar()}")
            
            # Sample some leads
            r5 = await conn.execute(text("SELECT * FROM civix.investigative_lead LIMIT 2;"))
            for row in r5.fetchall():
                print(dict(row._mapping))
        except Exception as e:
            print(f"investigative_lead error: {e}")

        # Check event_location table to understand linking
        try:
            r6 = await conn.execute(text("SELECT COUNT(*) FROM civix.event_location;"))
            print(f"\nEvent_location count: {r6.scalar()}")
            r7 = await conn.execute(text("SELECT * FROM civix.event_location LIMIT 2;"))
            for row in r7.fetchall():
                print(dict(row._mapping))
        except Exception as e:
            print(f"event_location error: {e}")

        # Check event_participant
        try:
            r8 = await conn.execute(text("SELECT COUNT(*) FROM civix.event_participant;"))
            print(f"\nEvent_participant count: {r8.scalar()}")
        except Exception as e:
            print(f"event_participant error: {e}")

        # How source_record links events to cases
        try:
            r9 = await conn.execute(text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema='civix' AND table_name='source_record' ORDER BY ordinal_position;"
            ))
            print("\n=== SOURCE_RECORD ===")
            for row in r9.fetchall():
                m = dict(row._mapping)
                print(f"  {m['column_name']} ({m['data_type']})")
            r10 = await conn.execute(text("SELECT COUNT(*) FROM civix.source_record;"))
            print(f"  Count: {r10.scalar()}")
        except Exception as e:
            print(f"source_record error: {e}")

asyncio.run(main())
