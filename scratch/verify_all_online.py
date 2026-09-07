import asyncio
import asyncpg
import urllib.request
import json

async def verify_all():
    print("==========================================================================")
    print("           CIVIX 2.0 SYSTEM AUDIT & SERVER HEALTH VERIFICATION           ")
    print("==========================================================================")

    # 1. PostgreSQL Check
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
        case_count = await conn.fetchval("SELECT count(*) FROM civix.investigative_case;")
        print(f"[ONLINE] PostgreSQL 16 DB (civix_demo): {case_count} cases loaded.")
        await conn.close()
    except Exception as e:
        print(f"[OFFLINE] PostgreSQL DB Error: {e}")

    # 2. Neo4j Check
    try:
        req = urllib.request.Request("http://localhost:7475/")
        with urllib.request.urlopen(req, timeout=5) as res:
            print(f"[ONLINE] Neo4j 5.23 Graph DBMS: responding on bolt://localhost:7688 (HTTP {res.getcode()})")
    except Exception as e:
        print(f"[OFFLINE] Neo4j Server Check Error: {e}")

    # 3. FastAPI Backend Check
    try:
        req = urllib.request.Request("http://localhost:8000/health")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read())
            print(f"[ONLINE] FastAPI Backend API: responding on http://localhost:8000/health ({data})")
    except Exception as e:
        print(f"[OFFLINE] FastAPI Backend Error: {e}")

    # 4. Vite Frontend Check
    try:
        req = urllib.request.Request("http://localhost:5173/")
        with urllib.request.urlopen(req, timeout=5) as res:
            print(f"[ONLINE] Vite Frontend Dev Server: responding on http://localhost:5173/ (HTTP {res.getcode()})")
    except Exception as e:
        print(f"[OFFLINE] Vite Frontend Error: {e}")

    print("==========================================================================")

if __name__ == "__main__":
    asyncio.run(verify_all())
