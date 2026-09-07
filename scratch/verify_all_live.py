import urllib.request
import json
import asyncio
import asyncpg
from neo4j import GraphDatabase

def test_http_endpoint(url, description):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Civix-Health-Checker'})
        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.getcode()
            print(f"[ONLINE] {description} ({url}) -> HTTP {status}")
            return True
    except urllib.error.HTTPError as e:
        # HTTP 401/403 is expected for protected routes without JWT token, but confirms backend router is live!
        if e.code in [401, 403]:
            print(f"[ONLINE - PROTECTED] {description} ({url}) -> HTTP {e.code} (Auth Protected Endpoint Live)")
            return True
        print(f"[OFFLINE] {description} ({url}) -> HTTP {e.code}")
        return False
    except Exception as e:
        print(f"[OFFLINE] {description} ({url}) -> Error: {e}")
        return False

async def test_postgres():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@127.0.0.1:5432/civix_demo')
        cases = await conn.fetchval('SELECT count(*) FROM civix.investigative_case;')
        users = await conn.fetchval('SELECT count(*) FROM civix.civix_user;')
        await conn.close()
        print(f"[ONLINE] PostgreSQL (port 5432 / civix_demo) -> {cases} Cases, {users} Users verified.")
        return True
    except Exception as e:
        print(f"[OFFLINE] PostgreSQL (port 5432) -> Error: {e}")
        return False

def test_neo4j():
    try:
        driver = GraphDatabase.driver('bolt://127.0.0.1:7688', auth=('neo4j', 'password'))
        with driver.session() as session:
            n_count = session.run('MATCH (n) RETURN count(n) AS count').single()['count']
            r_count = session.run('MATCH ()-[r]->() RETURN count(r) AS count').single()['count']
            print(f"[ONLINE] Neo4j Demo Graph (port 7688) -> {n_count} Nodes, {r_count} Relationships verified.")
        driver.close()
        return True
    except Exception as e:
        print(f"[OFFLINE] Neo4j Demo Graph (port 7688) -> Error: {e}")
        return False

def main():
    print("==========================================================================")
    print("                 CIVIX 2.0 FULL SYSTEM HEALTH & LIVE AUDIT                ")
    print("==========================================================================")
    asyncio.run(test_postgres())
    test_neo4j()
    test_http_endpoint("http://localhost:8000/health", "FastAPI Backend Health")
    test_http_endpoint("http://localhost:8000/api/v1/spatial/cases", "FastAPI Spatial Cases API")
    test_http_endpoint("http://localhost:8000/api/v1/cctv/streams", "FastAPI CCTV API")
    test_http_endpoint("http://localhost:5173/", "Vite Frontend Server")
    print("==========================================================================")

if __name__ == "__main__":
    main()
