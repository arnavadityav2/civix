import asyncio
from sqlalchemy import text
from civix_api.database import engine

async def audit_event_case_links():
    async with engine.connect() as conn:
        print("=== Event table structure ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event'
        """))
        print([r[0] for r in res.fetchall()])

        print("\n=== Event Location table structure ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event_location'
        """))
        print([r[0] for r in res.fetchall()])

        print("\n=== Event Participant table structure ===")
        res = await conn.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'event_participant'
        """))
        print([r[0] for r in res.fetchall()])

        # How many distinct events in event_location vs event
        res = await conn.execute(text("""
            SELECT 
                (SELECT count(*) FROM civix.event) as total_events,
                (SELECT count(distinct event_id) FROM civix.event_location WHERE case_id IS NOT NULL) as events_in_event_loc,
                (SELECT count(*) FROM civix.event_location WHERE case_id IS NOT NULL) as event_loc_rows
        """))
        print("Event counts:", res.fetchone())

        # Check if events have source_record_id linked to case or source_record
        res = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='source_record'
        """))
        print("source_record columns:", [r[0] for r in res.fetchall()])

        # Check if any other table links event to case
        res = await conn.execute(text("""
            SELECT tc.table_name, kcu.column_name, ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name 
            FROM information_schema.table_constraints AS tc 
            JOIN information_schema.key_column_usage AS kcu
              ON tc.constraint_name = kcu.constraint_name
              AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
              ON ccu.constraint_name = tc.constraint_name
              AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='civix'
              AND (tc.table_name='event' OR ccu.table_name='event');
        """))
        print("FKs on event:", res.fetchall())

if __name__ == "__main__":
    asyncio.run(audit_event_case_links())
