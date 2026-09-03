import asyncio
import time
from neo4j import GraphDatabase, AsyncGraphDatabase
import os

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

async def wait_for_neo4j():
    print("Waiting for Neo4j to start...")
    for _ in range(30):
        try:
            driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
            async with driver.session() as session:
                result = await session.run("RETURN 1 AS health")
                record = await result.single()
                if record and record["health"] == 1:
                    print("Neo4j is UP and running!")
                    await driver.close()
                    return True
        except Exception as e:
            time.sleep(2)
    print("Timed out waiting for Neo4j.")
    return False

async def apply_schema():
    print("Applying schema...")
    schema_path = os.path.join(os.path.dirname(__file__), '..', 'database', 'schema_neo4j.cypher')
    with open(schema_path, 'r') as f:
        schema_queries = f.read().split(';')
    
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    async with driver.session() as session:
        for query in schema_queries:
            query = query.strip()
            if query:
                try:
                    await session.run(query)
                except Exception as e:
                    print(f"Schema execution issue (might be acceptable if already exists): {e}")
        
        # Verify Constraints
        print("Verifying Constraints:")
        result = await session.run("SHOW CONSTRAINTS")
        records = await result.data()
        for record in records:
            print(f"- {record.get('name')}: {record.get('labelsOrTypes')} {record.get('properties')}")
            
    await driver.close()
    print("Schema setup and verification complete.")

if __name__ == "__main__":
    asyncio.run(wait_for_neo4j())
    asyncio.run(apply_schema())
