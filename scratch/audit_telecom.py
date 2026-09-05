import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from neo4j import GraphDatabase

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

async def audit_postgres():
    print("=================== POSTGRESQL AUDIT ===================")
    engine = create_async_engine(DB_URL)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    
    async with async_session() as session:
        # 1. Total Telecom Records / Entities
        print("\\n--- ENTITIES ---")
        res = await session.execute(text("SELECT entity_type, COUNT(*) FROM civix.entity GROUP BY entity_type ORDER BY count DESC"))
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        # 2. Total Locations (Towers vs Others)
        print("\\n--- LOCATIONS ---")
        res = await session.execute(text("SELECT location_type, COUNT(*) FROM civix.location GROUP BY location_type"))
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        print("\\n--- TOWER DETAILS ---")
        res = await session.execute(text("SELECT COUNT(*) FROM civix.location WHERE location_name ILIKE '%tower%' OR location_name ILIKE '%cell%'"))
        print(f"Locations with 'tower' or 'cell' in name: {res.scalar()}")
        
        # 3. Events
        print("\\n--- EVENTS ---")
        res = await session.execute(text("SELECT event_type, COUNT(*) FROM civix.event GROUP BY event_type ORDER BY count DESC"))
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        # 4. Event Participants (Roles)
        print("\\n--- EVENT PARTICIPANT ROLES ---")
        res = await session.execute(text("SELECT participant_role, COUNT(*) FROM civix.event_participant GROUP BY participant_role ORDER BY count DESC"))
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        # 5. Evidence
        print("\\n--- EVIDENCE (Skipped) ---")
            
        # 6. Specific Telecom Event Breakdown
        print("\\n--- TELECOM EVENTS / PINGS ---")
        res = await session.execute(text("""
            SELECT e.event_id, e.event_type, e.occurred_at, l.location_name 
            FROM civix.event e
            JOIN civix.event_participant ep ON e.event_id = ep.event_id AND ep.participant_role = 'LOCATION'
            JOIN civix.location l ON ep.entity_id = l.entity_id
            WHERE e.event_type IN ('DEVICE_PING', 'CALL', 'MESSAGE')
            LIMIT 10
        """))
        for row in res:
            print(f"{row[0]} | {row[1]} | {row[2]} | {row[3]}")
            
        # 7. Check if phone/device entities have MSISDN/IMEI/IMSI properties
        print("\\n--- ENTITY ATTRIBUTES ---")
        res = await session.execute(text("""
            SELECT entity_type, COUNT(*) 
            FROM civix.entity 
            WHERE entity_type IN ('PHONE_NUMBER', 'DEVICE', 'SIM') 
            GROUP BY entity_type
        """))
        for row in res:
            print(f"{row[0]}: {row[1]}")
            
        # 8. Golden Cases Context
        print("\\n--- TELECOM EVENTS TOTAL ---")
        res = await session.execute(text("""
            SELECT e.event_type, COUNT(DISTINCT e.event_id) as telecom_events
            FROM civix.event e
            WHERE e.event_type IN ('DEVICE_PING', 'CALL', 'MESSAGE')
            GROUP BY e.event_type
        """))
        for row in res:
            print(f"{row[0]} | Events: {row[1]}")

    await engine.dispose()

def audit_neo4j():
    print("\\n=================== NEO4J AUDIT ===================")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        print("\\n--- NODE LABELS ---")
        res = session.run("CALL db.labels()")
        for record in res:
            print(record[0])
            
        print("\\n--- RELATIONSHIP TYPES ---")
        res = session.run("CALL db.relationshipTypes()")
        for record in res:
            print(record[0])
            
        print("\\n--- RELATIONSHIP COUNTS ---")
        res = session.run("""
            MATCH ()-[r]->() 
            WHERE type(r) IN ['CALLED', 'MESSAGED', 'PINGED_TOWER', 'USED_DEVICE', 'USED_SIM', 'LOCATED_AT']
            RETURN type(r), count(r) ORDER BY count(r) DESC
        """)
        for record in res:
            print(f"{record[0]}: {record[1]}")
            
    driver.close()

if __name__ == "__main__":
    asyncio.run(audit_postgres())
    audit_neo4j()
