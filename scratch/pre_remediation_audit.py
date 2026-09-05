#!/usr/bin/env python3
"""Deep audit of synthetic case event/lead state pre-remediation."""
import asyncio, sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        # Key insight: events link to cases via event_location.case_id
        # Let's verify that linkage
        
        # 1. How many synthetic cases have events (via event_location)?
        r1 = await conn.execute(text("""
            SELECT COUNT(DISTINCT el.case_id) as cases_with_event_locations,
                   COUNT(DISTINCT el.event_id) as total_events_with_location,
                   COUNT(*) as total_event_locations
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%';
        """))
        row = r1.fetchone()
        m = dict(row._mapping)
        print(f"Synthetic cases with event_locations: {m['cases_with_event_locations']}")
        print(f"Total synthetic events with location: {m['total_events_with_location']}")
        print(f"Total synthetic event_location records: {m['total_event_locations']}")

        # 2. Any synthetic events where all events share same location?
        r2 = await conn.execute(text("""
            SELECT el.case_id::text, COUNT(DISTINCT el.location_id) as distinct_locations, COUNT(el.event_id) as event_count
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%'
            GROUP BY el.case_id
            ORDER BY distinct_locations ASC
            LIMIT 10;
        """))
        print("\nSample synthetic cases (distinct locations per case):")
        for row in r2.fetchall():
            m = dict(row._mapping)
            print(f"  case_id={m['case_id'][:8]}... distinct_locs={m['distinct_locations']} events={m['event_count']}")

        # 3. Check location coords for a sample synthetic case
        r3 = await conn.execute(text("""
            SELECT c.case_number, l.location_name,
                   ST_X(l.coordinates::geometry) as lon,
                   ST_Y(l.coordinates::geometry) as lat
            FROM civix.event_location el
            JOIN civix.investigative_case c ON el.case_id = c.case_id
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE c.case_number LIKE 'SYN-%'
            LIMIT 10;
        """))
        print("\nSample synthetic event locations with coordinates:")
        for row in r3.fetchall():
            m = dict(row._mapping)
            print(f"  {m['case_number']}: {m['location_name']} lat={m['lat']:.4f} lon={m['lon']:.4f}")

        # 4. How many synthetic cases have investigative leads?
        r4 = await conn.execute(text("""
            SELECT COUNT(DISTINCT il.case_id) as cases_with_leads,
                   COUNT(*) as total_leads
            FROM civix.investigative_lead il
            JOIN civix.investigative_case c ON il.case_id = c.case_id
            WHERE c.case_number LIKE 'SYN-%';
        """))
        row = r4.fetchone()
        m = dict(row._mapping)
        print(f"\nSynthetic cases with leads: {m['cases_with_leads']}")
        print(f"Total synthetic leads: {m['total_leads']}")

        # 5. Check available enum values
        r5 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.lead_status_enum))::text;"))
        lead_statuses = [row[0] for row in r5.fetchall()]
        print(f"\nLead statuses: {lead_statuses}")

        r6 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.lead_priority_enum))::text;"))
        lead_priorities = [row[0] for row in r6.fetchall()]
        print(f"Lead priorities: {lead_priorities}")

        r7 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.event_type_enum))::text;"))
        event_types = [row[0] for row in r7.fetchall()]
        print(f"Event types: {event_types}")

        r8 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.participant_role_enum))::text;"))
        participant_roles = [row[0] for row in r8.fetchall()]
        print(f"Participant roles: {participant_roles}")

        r9 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.location_predicate_enum))::text;"))
        loc_predicates = [row[0] for row in r9.fetchall()]
        print(f"Location predicates: {loc_predicates}")

        r10 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.epistemic_status_enum))::text;"))
        ep_statuses = [row[0] for row in r10.fetchall()]
        print(f"Epistemic statuses: {ep_statuses}")

        # 6. Check entity_role enum
        r11 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.entity_role_enum))::text;"))
        entity_roles = [row[0] for row in r11.fetchall()]
        print(f"Entity roles: {entity_roles}")

        # 7. Check location table schema
        r12 = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='location' ORDER BY ordinal_position;"
        ))
        print("\n=== LOCATION TABLE ===")
        for row in r12.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']})")

        # 8. Check location_type enum
        try:
            r13 = await conn.execute(text("SELECT unnest(enum_range(NULL::civix.location_type_enum))::text;"))
            loc_types = [row[0] for row in r13.fetchall()]
            print(f"Location types: {loc_types}")
        except Exception as e:
            print(f"location_type_enum error: {e}")

        # 9. Total synthetic cases count
        r14 = await conn.execute(text("SELECT COUNT(*) FROM civix.investigative_case WHERE case_number LIKE 'SYN-%';"))
        print(f"\nTotal SYN- cases: {r14.scalar()}")

        # 10. Check generation_run table
        r15 = await conn.execute(text(
            "SELECT column_name, data_type FROM information_schema.columns "
            "WHERE table_schema='civix' AND table_name='generation_run' ORDER BY ordinal_position;"
        ))
        print("\n=== GENERATION_RUN TABLE ===")
        for row in r15.fetchall():
            m = dict(row._mapping)
            print(f"  {m['column_name']} ({m['data_type']})")

        # Get latest generation_run
        try:
            r16 = await conn.execute(text("SELECT generation_run_id, run_label, created_at FROM civix.generation_run ORDER BY created_at DESC LIMIT 3;"))
            print("Recent generation_run records:")
            for row in r16.fetchall():
                m = dict(row._mapping)
                print(f"  {m}")
        except Exception as e:
            print(f"generation_run error: {e}")

asyncio.run(main())
