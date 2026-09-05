import asyncio
import asyncpg
from neo4j import AsyncGraphDatabase
import json

DB_URL = "postgresql://postgres:postgres@localhost:5432/civix_demo"
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

async def main():
    print("============================================================")
    print("GRAPH PROJECTION SAFETY REVIEW DATA")
    print("============================================================\n")

    conn = await asyncpg.connect(DB_URL)
    
    print("1. CURRENT NEO4J STATE")
    try:
        driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        async with driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) as node_count")
            record = await result.single()
            print(f"Total Nodes: {record['node_count']}")
            
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            record = await result.single()
            print(f"Total Relationships: {record['rel_count']}")
            
            result = await session.run("CALL db.labels()")
            records = await result.data()
            print(f"Labels: {[r['label'] for r in records]}")
            
            result = await session.run("CALL db.relationshipTypes()")
            records = await result.data()
            print(f"Relationship Types: {[r['relationshipType'] for r in records]}")
        await driver.close()
    except Exception as e:
        print(f"Neo4j error: {e}")
        
    print("\n2. CURRENT PENDING OUTBOX INVENTORY")
    rows = await conn.fetch("""
        SELECT entity_type, error_status, retry_count, COUNT(*) 
        FROM civix.outbox 
        WHERE consumed_at IS NULL 
        GROUP BY entity_type, error_status, retry_count
        ORDER BY entity_type
    """)
    for r in rows:
        print(dict(r))
        
    print("\n4. EVIDENCE RELATIONSHIP INVENTORY")
    artifact_count = await conn.fetchval("SELECT count(*) FROM civix.evidence_artifact")
    instance_count = await conn.fetchval("SELECT count(*) FROM civix.evidence_instance")
    print(f"Evidence Artifacts: {artifact_count}")
    print(f"Evidence Instances: {instance_count}")
    
    instance_schema = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='evidence_instance'")
    print(f"Evidence Instance schema references: {[dict(r) for r in instance_schema if '_id' in r['column_name']]}")

    print("\n5. EVENT PROJECTION INVENTORY")
    event_count = await conn.fetchval("SELECT count(*) FROM civix.event")
    event_part_count = await conn.fetchval("SELECT count(*) FROM civix.event_participant")
    event_loc_count = await conn.fetchval("SELECT count(*) FROM civix.event_location")
    print(f"Events in PostgreSQL: {event_count}")
    print(f"Event Participants in PostgreSQL: {event_part_count}")
    print(f"Event Locations in PostgreSQL: {event_loc_count}")

    print("\n6. FIR PROJECTION INVENTORY")
    fir_count = await conn.fetchval("SELECT count(*) FROM civix.fir")
    print(f"FIRs in PostgreSQL: {fir_count}")
    
    print("\n7. LEAD PROJECTION INVENTORY")
    lead_count = await conn.fetchval("SELECT count(*) FROM civix.investigative_lead")
    print(f"Leads in PostgreSQL: {lead_count}")
    
    print("\n8. ASSERTION PROJECTION INVENTORY")
    assertion_count = await conn.fetchval("SELECT count(*) FROM civix.assertion")
    print(f"Assertions in PostgreSQL: {assertion_count}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
