"""
Phase A Supplemental Audit - CALL relationship deep-dive and event_location full map
"""
import asyncio
import sys
sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

async def run():
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:

        # CALL event - deep dive on event_location linkage
        print("=== CALL events via event_location ===")
        r = await session.execute(text("""
            SELECT COUNT(DISTINCT e.event_id) as linked_calls,
                   COUNT(DISTINCT el.location_id) as unique_locations,
                   COUNT(DISTINCT el.case_id) as unique_cases
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            WHERE e.event_type = 'CALL'
        """))
        row = r.fetchone()
        print(f"  CALL linked via event_location: events={row[0]}, locations={row[1]}, cases={row[2]}")
        
        # CALL participant detail 
        print("\n=== ALL CALL PARTICIPANTS (first 10 events) ===")
        r = await session.execute(text("""
            SELECT e.event_id, e.occurred_at, ep.participant_role, ent.entity_type, ep.entity_id
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity ent ON ep.entity_id = ent.entity_id
            WHERE e.event_type = 'CALL'
            LIMIT 20
        """))
        for row in r.fetchall():
            print(f"  event={str(row[0])[:8]} occurred={row[1]} role={row[2]} ent_type={row[3]}")
        
        # What is the "PARTICIPANT" role exactly? 
        # Let's see: for CALL events with PARTICIPANT role, what entity types are involved?
        print("\n=== CALL PARTICIPANT entity types ===")
        r = await session.execute(text("""
            SELECT ent.entity_type, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity ent ON ep.entity_id = ent.entity_id
            WHERE e.event_type = 'CALL' AND ep.participant_role = 'PARTICIPANT'
            GROUP BY ent.entity_type
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")
        
        # DEVICE_PING: what participant roles exist?
        print("\n=== DEVICE_PING PARTICIPANT DETAIL ===")
        r = await session.execute(text("""
            SELECT ep.participant_role, ent.entity_type, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id
            JOIN civix.entity ent ON ep.entity_id = ent.entity_id
            WHERE e.event_type = 'DEVICE_PING'
            GROUP BY ep.participant_role, ent.entity_type
        """))
        for row in r.fetchall():
            print(f"  role={row[0]} entity_type={row[1]}: {row[2]}")
        
        # DEVICE_PING via event_location - what location types are linked?
        print("\n=== DEVICE_PING event_location → location types ===")
        r = await session.execute(text("""
            SELECT l.location_type, l.location_name, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE e.event_type = 'DEVICE_PING'
            GROUP BY l.location_type, l.location_name
            ORDER BY cnt DESC
            LIMIT 20
        """))
        for row in r.fetchall():
            print(f"  type={row[0]}, name={row[1]}: {row[2]}")

        # How many CELL_SECTOR_POLYGON locations are in event_location?
        print("\n=== CELL_SECTOR_POLYGON in event_location (ALL event types) ===")
        r = await session.execute(text("""
            SELECT e.event_type, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE l.location_type = 'CELL_SECTOR_POLYGON'
            GROUP BY e.event_type
            ORDER BY cnt DESC
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # CALL event has description - does it contain CDR metadata?
        print("\n=== CALL event descriptions (first 5) ===")
        r = await session.execute(text("""
            SELECT e.event_id, e.description
            FROM civix.event e
            WHERE e.event_type = 'CALL' AND e.description IS NOT NULL
            LIMIT 5
        """))
        for row in r.fetchall():
            print(f"  {str(row[0])[:8]}: {str(row[1])[:200]}")

        # CALL events with source_record - check if source_record has CDR data
        print("\n=== CALL source_record types ===")
        r = await session.execute(text("""
            SELECT sr.record_type, COUNT(*) as cnt
            FROM civix.event e
            JOIN civix.source_record sr ON e.source_record_id = sr.source_record_id
            WHERE e.event_type = 'CALL'
            GROUP BY sr.record_type
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # How many CALL events have no source_record?
        r = await session.execute(text("""
            SELECT 
                COUNT(*) FILTER (WHERE source_record_id IS NOT NULL) as with_src,
                COUNT(*) FILTER (WHERE source_record_id IS NULL) as without_src
            FROM civix.event WHERE event_type='CALL'
        """))
        row = r.fetchone()
        print(f"\n  CALL with source_record: {row[0]}, without: {row[1]}")

        # assertion table - do we have CALLED/MESSAGED predicates?
        print("\n=== Assertions with telecom predicates ===")
        r = await session.execute(text("""
            SELECT predicate, COUNT(*) as cnt
            FROM civix.assertion
            WHERE predicate IN ('CALLED', 'MESSAGED', 'PINGED_TOWER', 'USED_DEVICE', 'USED_SIM', 'HAD_NUMBER')
            GROUP BY predicate
            ORDER BY cnt DESC
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

        # Check if there are IMSI values in sim table
        print("\n=== SIM IMSI population ===")
        r = await session.execute(text("""
            SELECT 
                COUNT(*) as total_sims,
                COUNT(imsi) as with_imsi,
                COUNT(iccid) as with_iccid
            FROM civix.sim
        """))
        row = r.fetchone()
        print(f"  Total SIMs: {row[0]}, with IMSI: {row[1]}, with ICCID: {row[2]}")

        # Device IMEI population
        print("\n=== DEVICE IMEI population ===")
        r = await session.execute(text("""
            SELECT 
                COUNT(*) as total_devices,
                COUNT(imei) as with_imei,
                COUNT(mac_address) as with_mac
            FROM civix.device
        """))
        row = r.fetchone()
        print(f"  Total devices: {row[0]}, with IMEI: {row[1]}, with MAC: {row[2]}")

        # Hero cases - what telecom events do they have?
        print("\n=== HERO CASES TELECOM EVENTS ===")
        r = await session.execute(text("""
            SELECT ic.case_number, e.event_type, COUNT(*) as cnt
            FROM civix.investigative_case ic
            JOIN civix.event_location el ON ic.case_id = el.case_id
            JOIN civix.event e ON el.event_id = e.event_id
            WHERE e.event_type IN ('CALL', 'DEVICE_PING', 'MESSAGE')
            AND ic.case_number IN (
                SELECT case_number FROM civix.investigative_case 
                ORDER BY case_number LIMIT 13
            )
            GROUP BY ic.case_number, e.event_type
            ORDER BY ic.case_number
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}={row[2]}")

        # Check the actual link between CALL event_location and a real tower
        print("\n=== CALL event_location → CELL_SECTOR_POLYGON sample ===")
        r = await session.execute(text("""
            SELECT e.event_id, el.case_id, l.location_name, l.location_type
            FROM civix.event e
            JOIN civix.event_location el ON e.event_id = el.event_id
            JOIN civix.location l ON el.location_id = l.entity_id
            WHERE e.event_type = 'CALL' AND l.location_type = 'CELL_SECTOR_POLYGON'
            LIMIT 10
        """))
        for row in r.fetchall():
            print(f"  event={str(row[0])[:8]} case={str(row[1])[:8]} tower={row[2]} type={row[3]}")

        # source_record CDR_ROW count
        print("\n=== CDR_ROW source records ===")
        r = await session.execute(text("""
            SELECT record_type, COUNT(*) 
            FROM civix.source_record 
            GROUP BY record_type 
            ORDER BY count DESC
            LIMIT 20
        """))
        for row in r.fetchall():
            print(f"  {row[0]}: {row[1]}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
