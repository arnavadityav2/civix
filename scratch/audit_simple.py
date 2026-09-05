#!/usr/bin/env python3
"""Simple step-by-step audit for investigative semantics remediation."""
import asyncio, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def q(conn, sql, label=""):
    try:
        r = await conn.execute(text(sql))
        rows = r.fetchall()
        if label:
            print(f"\n--- {label} ---")
        for row in rows:
            print(dict(row._mapping))
        return rows
    except Exception as e:
        print(f"\n--- {label} ERROR: {e} ---")
        return []

async def main():
    async with engine.connect() as conn:
        # 1. Location table columns
        await q(conn,
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='location' ORDER BY ordinal_position;",
            "LOCATION TABLE COLUMNS"
        )

        # 2. Synthetic case event counts (via event_location.case_id)
        await q(conn, """
            SELECT COUNT(DISTINCT el.case_id) as syn_cases_with_event_locs,
                   COUNT(DISTINCT el.event_id) as unique_events,
                   COUNT(*) as total_event_loc_records
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
        """, "SYNTHETIC EVENT COVERAGE")

        # 3. How many total synthetic cases
        await q(conn, "SELECT COUNT(*) as syn_total FROM civix.investigative_case WHERE case_number LIKE 'SYN-%'", "SYNTHETIC CASE COUNT")

        # 4. Synthetic cases with investigative_lead
        await q(conn, """
            SELECT COUNT(DISTINCT il.case_id) as syn_cases_with_leads, COUNT(*) as total_syn_leads
            FROM civix.investigative_lead il
            JOIN civix.investigative_case c ON il.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
        """, "SYNTHETIC LEAD COVERAGE")

        # 5. Enums
        await q(conn, "SELECT unnest(enum_range(NULL::civix.lead_status_enum))::text as val;", "LEAD STATUS ENUM")
        await q(conn, "SELECT unnest(enum_range(NULL::civix.lead_priority_enum))::text as val;", "LEAD PRIORITY ENUM")
        await q(conn, "SELECT unnest(enum_range(NULL::civix.event_type_enum))::text as val;", "EVENT TYPE ENUM")
        await q(conn, "SELECT unnest(enum_range(NULL::civix.participant_role_enum))::text as val;", "PARTICIPANT ROLE ENUM")
        await q(conn, "SELECT unnest(enum_range(NULL::civix.location_predicate_enum))::text as val;", "LOCATION PREDICATE ENUM")
        await q(conn, "SELECT unnest(enum_range(NULL::civix.epistemic_status_enum))::text as val;", "EPISTEMIC STATUS ENUM")
        await q(conn, "SELECT unnest(enum_range(NULL::civix.entity_role_enum))::text as val;", "ENTITY ROLE ENUM")

        # 6. Generation run info
        await q(conn, "SELECT generation_run_id::text, run_label, created_at FROM civix.generation_run ORDER BY created_at DESC LIMIT 3;", "RECENT GENERATION RUNS")

        # 7. Sample of a synthetic case with its entities, to understand cross-case
        await q(conn, """
            SELECT c.case_number, cer.entity_id::text, cer.role
            FROM civix.investigative_case c
            JOIN civix.case_entity_role cer ON c.case_id = cer.case_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 5
        """, "SAMPLE SYNTHETIC CASE ENTITIES")

        # 8. Sample location record
        await q(conn, "SELECT * FROM civix.location LIMIT 1;", "SAMPLE LOCATION RECORD")

        # 9. Check fir count for synthetics
        await q(conn, """
            SELECT COUNT(*) as syn_firs FROM civix.fir f
            JOIN civix.investigative_case c ON f.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
        """, "SYNTHETIC FIR COUNT")

        # 10. Check event table for synthetic event records (via event_location)
        await q(conn, """
            SELECT e.event_type, e.description, e.occurred_at
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 3
        """, "SAMPLE SYNTHETIC EVENTS")

        # 11. Check how many synthetic events have descriptions starting with generic text
        await q(conn, """
            SELECT COUNT(*) as generic_events FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            AND (e.description LIKE 'Synthetic%' OR e.description LIKE 'Event%' OR e.description IS NULL)
        """, "GENERIC/NULL EVENT DESCRIPTIONS")

asyncio.run(main())
