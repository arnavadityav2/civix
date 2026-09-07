import asyncio
import asyncpg
import urllib.request
import json
from neo4j import GraphDatabase

async def full_audit():
    print("=================================================================")
    print("             CIVIX 2.0 FULL SYSTEM & SESSIONS STATUS             ")
    print("=================================================================")
    
    # PostgreSQL
    try:
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
        tables = await conn.fetchval("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")
        cases = await conn.fetchval("SELECT count(*) FROM investigative_cases;") if await conn.fetchval("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'investigative_cases');") else 0
        await conn.close()
        print(f"[ONLINE] PostgreSQL (Port 5432)   | Database: civix_demo | Tables: {tables} | Active Cases: {cases}")
    except Exception as e:
        print(f"[OFFLINE] PostgreSQL (Port 5432)  | Error: {e}")
        
    # Neo4j
    try:
        driver = GraphDatabase.driver("bolt://127.0.0.1:7688", auth=("neo4j", "password"))
        with driver.session() as session:
            count = session.run("MATCH (n) RETURN count(n) AS c").single()["c"]
        driver.close()
        print(f"[ONLINE] Neo4j Graph (Port 7688)  | Instance: civix_demo_graph | Total Nodes: {count}")
    except Exception as e:
        print(f"[OFFLINE] Neo4j Graph (Port 7688) | Error: {e}")
        
    # FastAPI Backend
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/health", timeout=2)
        res = json.loads(req.read().decode())
        print(f"[ONLINE] FastAPI Backend (Port 8000)| Health: {res}")
    except Exception as e:
        print(f"[OFFLINE] FastAPI Backend (8000)  | Error: {e}")
        
    # Vite Frontend
    try:
        req = urllib.request.urlopen("http://localhost:5173", timeout=2)
        code = req.getcode()
        print(f"[ONLINE] Vite Frontend (Port 5173) | Status: HTTP {code}")
    except Exception as e:
        print(f"[OFFLINE] Vite Frontend (5173)    | Error: {e}")
        
    print("=================================================================")

if __name__ == "__main__":
    asyncio.run(full_audit())
