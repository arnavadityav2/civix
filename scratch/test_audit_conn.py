import asyncio
import json
import os
import asyncpg
from neo4j import GraphDatabase

DB_URL = "postgresql://postgres:postgres@localhost:5432/civix_demo"
NEO4J_URI = "bolt://localhost:7688"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"

def test_neo4j():
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            record = result.single()
            print(f"Neo4j Connected successfully! Total nodes: {record['total_nodes']}")
        driver.close()
        return True
    except Exception as e:
        print(f"Neo4j Connection Error: {e}")
        return False

async def main():
    print("Testing PostgreSQL...")
    conn = await asyncpg.connect(DB_URL)
    val = await conn.fetchval("SELECT count(*) FROM civix.investigative_case;")
    print(f"PostgreSQL Connected! Total cases: {val}")
    await conn.close()
    
    print("Testing Neo4j...")
    test_neo4j()

if __name__ == "__main__":
    asyncio.run(main())
