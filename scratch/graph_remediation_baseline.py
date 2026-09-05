import asyncio
import os
import json
import asyncpg
from neo4j import AsyncGraphDatabase

DB_URL = "postgresql://postgres:postgres@localhost:5432/civix_demo"
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

async def main():
    print("=== POSTGRESQL BASELINE ===")
    conn = await asyncpg.connect(DB_URL)
    tables = [
        "investigative_case",
        "entity",
        "case_entity_role",
        "event",
        "event_participant",
        "event_location",
        "assertion",
        "investigative_lead",
        "fir",
        "evidence_artifact",
        "evidence_instance",
        "phone_number",
        "sim",
        "device",
        "financial_account",
        "property",
        "vehicle",
        "organization",
        "location"
    ]
    for table in tables:
        try:
            val = await conn.fetchval(f"SELECT count(*) FROM civix.{table}")
            print(f"{table}: {val}")
        except Exception as e:
            print(f"{table}: Error - {e}")
            
    await conn.close()
    
    print("\n=== NEO4J BASELINE ===")
    try:
        driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, "neo4j"))
        async with driver.session() as session:
            result = await session.run("MATCH (n) RETURN count(n) as node_count")
            record = await result.single()
            print(f"Node count: {record['node_count']}")
            
            result = await session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            record = await result.single()
            print(f"Relationship count: {record['rel_count']}")
            
            result = await session.run("CALL db.labels()")
            records = await result.data()
            print(f"Labels: {[r['label'] for r in records]}")
            
            result = await session.run("CALL db.relationshipTypes()")
            records = await result.data()
            print(f"Relationship Types: {[r['relationshipType'] for r in records]}")
            
        await driver.close()
    except Exception as e:
        print(f"Neo4j error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
