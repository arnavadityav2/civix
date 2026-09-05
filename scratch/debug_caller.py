"""
Debug: Why does SYN-2025-002 show caller=None in events?
"""
import asyncio, sys
sys.stdout.reconfigure(encoding="utf-8")
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

async def run():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with async_session() as s:
        # Get the CALL event for SYN-2025-002
        r = await s.execute(text("""
            SELECT e.event_id, e.occurred_at, e.description
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.investigative_case ic ON el.case_id = ic.case_id
            WHERE ic.case_number = 'SYN-2025-002' AND e.event_type = 'CALL'
        """))
        rows = r.fetchall()
        print("=== CALL events for SYN-2025-002 ===")
        for row in rows:
            print(f"  event_id={row[0]}, occurred_at={row[1]}")
        
        if rows:
            eid = rows[0][0]
            # Get all participants
            r2 = await s.execute(text("""
                SELECT ep.participant_role, ent.entity_type, ep.entity_id,
                       pn.msisdn, per.display_name
                FROM civix.event_participant ep
                JOIN civix.entity ent ON ep.entity_id = ent.entity_id
                LEFT JOIN civix.phone_number pn ON ep.entity_id = pn.entity_id
                LEFT JOIN civix.person per ON ep.entity_id = per.entity_id
                WHERE ep.event_id = :eid
            """), {"eid": eid})
            print(f"\n=== Participants for CALL event {eid} ===")
            for row in r2.fetchall():
                print(f"  role={row[0]}, entity_type={row[1]}, msisdn={row[3]}, person={row[4]}")
            
            # Check duration via TSTZRANGE
            r3 = await s.execute(text("""
                SELECT lower(occurred_at), upper(occurred_at),
                       EXTRACT(EPOCH FROM (upper(occurred_at) - lower(occurred_at))) as dur
                FROM civix.event WHERE event_id = :eid
            """), {"eid": eid})
            row = r3.fetchone()
            print(f"\n=== Duration for CALL event ===")
            print(f"  lower={row[0]}, upper={row[1]}, duration_sec={row[2]}")

        # Check case_entity_role for SYN-2025-002
        r4 = await s.execute(text("""
            SELECT cer.role, ent.entity_type, COUNT(*) as cnt
            FROM civix.case_entity_role cer
            JOIN civix.entity ent ON cer.entity_id = ent.entity_id
            JOIN civix.investigative_case ic ON cer.case_id = ic.case_id
            WHERE ic.case_number = 'SYN-2025-002'
            GROUP BY cer.role, ent.entity_type
        """))
        print("\n=== case_entity_role for SYN-2025-002 ===")
        for row in r4.fetchall():
            print(f"  role={row[0]}, entity_type={row[1]}: {row[2]}")

        # Check ALL CALL events for CALLER/CALLEE roles
        r5 = await s.execute(text("""
            SELECT ep.participant_role, COUNT(*) as cnt
            FROM civix.event_participant ep
            JOIN civix.event e ON ep.event_id = e.event_id
            WHERE e.event_type = 'CALL'
            GROUP BY ep.participant_role
        """))
        print("\n=== CALL participant roles (ALL CALLS) ===")
        for row in r5.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # Check occurred_at upper_inf flag
        r6 = await s.execute(text("""
            SELECT event_id, upper_inf(occurred_at) as is_inf,
                   lower_inf(occurred_at) as low_inf,
                   lower(occurred_at), upper(occurred_at)
            FROM civix.event WHERE event_type = 'CALL' LIMIT 5
        """))
        print("\n=== CALL occurred_at sample ===")
        for row in r6.fetchall():
            print(f"  event_id={str(row[0])[:8]} is_inf={row[1]} low_inf={row[2]} lower={row[3]} upper={row[4]}")

    await engine.dispose()

asyncio.run(run())
