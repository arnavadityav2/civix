import asyncio
import asyncpg
from neo4j import GraphDatabase

async def check_pg():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
        tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix' ORDER BY table_name;")
        print("PostgreSQL Tables in 'civix' schema:")
        for t in tables:
            print(" -", t['table_name'])
        
        cases_cnt = await conn.fetchval("SELECT count(*) FROM civix.investigative_case;")
        print(f"\nTotal Cases in civix.investigative_case: {cases_cnt}")
        await conn.close()
    except Exception as e:
        print(f"PostgreSQL Check Error: {e}")

def check_neo4j():
    for port in [7688, 7687]:
        try:
            driver = GraphDatabase.driver(f"bolt://127.0.0.1:{port}", auth=("neo4j", "password"))
            with driver.session() as session:
                n_count = session.run("MATCH (n) RETURN count(n) AS count").single()["count"]
                r_count = session.run("MATCH ()-[r]->() RETURN count(r) AS count").single()["count"]
                print(f"\nNeo4j (port {port}) ONLINE:")
                print(f" - Nodes: {n_count}")
                print(f" - Relationships: {r_count}")
            driver.close()
            return
        except Exception as e:
            print(f"Neo4j Check Port {port}: {e}")

if __name__ == "__main__":
    asyncio.run(check_pg())
    check_neo4j()
