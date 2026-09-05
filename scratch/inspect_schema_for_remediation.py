#!/usr/bin/env python3
"""Inspect DB schema for the investigative semantics remediation."""
import asyncio, sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        # EVENT table schema
        r = await conn.execute(text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='event' "
            "ORDER BY ordinal_position;"
        ))
        print('=== EVENT TABLE SCHEMA ===')
        for row in r.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']}) nullable={m['is_nullable']}")

        # EVENT_LOCATION table schema
        r2 = await conn.execute(text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='event_location' "
            "ORDER BY ordinal_position;"
        ))
        print('\n=== EVENT_LOCATION TABLE SCHEMA ===')
        for row in r2.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']}) nullable={m['is_nullable']}")

        # INVESTIGATIVE_LEAD table schema
        r3 = await conn.execute(text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='investigative_lead' "
            "ORDER BY ordinal_position;"
        ))
        print('\n=== INVESTIGATIVE_LEAD TABLE SCHEMA ===')
        exists = False
        for row in r3.fetchall():
            exists = True
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']}) nullable={m['is_nullable']}")
        if not exists:
            print("  *** TABLE DOES NOT EXIST ***")

        # EVENT_PARTICIPANT table schema
        r4 = await conn.execute(text(
            "SELECT column_name, data_type, is_nullable "
            "FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='event_participant' "
            "ORDER BY ordinal_position;"
        ))
        print('\n=== EVENT_PARTICIPANT TABLE SCHEMA ===')
        for row in r4.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']}) nullable={m['is_nullable']}")

        # Event type enum values
        r5 = await conn.execute(text(
            "SELECT unnest(enum_range(NULL::civix.event_type_enum))::text;"
        ))
        print('\n=== EVENT TYPE ENUM VALUES ===')
        vals = [row[0] for row in r5.fetchall()]
        print(', '.join(vals))

        # Investigative lead enum values if table exists
        try:
            r6 = await conn.execute(text(
                "SELECT unnest(enum_range(NULL::civix.lead_status_enum))::text;"
            ))
            print('\n=== LEAD STATUS ENUM VALUES ===')
            vals = [row[0] for row in r6.fetchall()]
            print(', '.join(vals))
        except Exception as e:
            print(f'\n=== LEAD STATUS ENUM: {e} ===')

        try:
            r7 = await conn.execute(text(
                "SELECT unnest(enum_range(NULL::civix.lead_priority_enum))::text;"
            ))
            print('\n=== LEAD PRIORITY ENUM VALUES ===')
            vals = [row[0] for row in r7.fetchall()]
            print(', '.join(vals))
        except Exception as e:
            print(f'\n=== LEAD PRIORITY ENUM: {e} ===')

        # Actual count on investigative_lead
        try:
            r8 = await conn.execute(text(
                "SELECT COUNT(*) FROM civix.investigative_lead;"
            ))
            print(f'\n=== INVESTIGATIVE_LEAD COUNT: {r8.scalar()} ===')
        except Exception as e:
            print(f'\n=== INVESTIGATIVE_LEAD COUNT ERROR: {e} ===')

        # Check synthetic events
        r9 = await conn.execute(text("""
            SELECT COUNT(*) FROM civix.event e
            JOIN civix.investigative_case c ON e.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
        """))
        print(f'\n=== SYNTHETIC CASE EVENTS COUNT: {r9.scalar()} ===')

        # Check spatial coverage on events
        r10 = await conn.execute(text("""
            SELECT
                COUNT(DISTINCT e.case_id) as cases_with_events,
                COUNT(DISTINCT el.event_id) as events_with_location,
                COUNT(DISTINCT e.event_id) as total_events
            FROM civix.event e
            JOIN civix.investigative_case c ON e.case_id = c.case_id
            LEFT JOIN civix.event_location el ON e.event_id = el.event_id
            WHERE c.case_number LIKE 'SYN-%'
        """))
        row = r10.fetchone()
        if row:
            m = dict(row._mapping)
            print(f'\n=== SYNTHETIC EVENT SPATIAL COVERAGE ===')
            print(f"  cases_with_events: {m['cases_with_events']}")
            print(f"  events_with_location: {m['events_with_location']}")
            print(f"  total_events: {m['total_events']}")

asyncio.run(main())
