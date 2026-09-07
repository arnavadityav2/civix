import asyncio
import asyncpg
import socket

def check_port(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

async def main():
    print("=== CIVIX 2.0 SESSION & PORT STATUS AUDIT ===")
    
    # 1. Check Ports
    ports = {
        "PostgreSQL (5432)": ("localhost", 5432),
        "Neo4j Bolt (7687)": ("localhost", 7687),
        "Neo4j Bolt (7688)": ("localhost", 7688),
        "Neo4j HTTP (7474)": ("localhost", 7474),
        "FastAPI Backend (8000)": ("localhost", 8000),
        "Vite Frontend (5173)": ("localhost", 5173),
    }
    
    for name, (host, port) in ports.items():
        online = check_port(host, port)
        status = "ONLINE" if online else "OFFLINE"
        print(f"[{status}] {name}")

    print("\n=== POSTGRESQL DETAILED STATUS ===")
    try:
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/postgres")
        dbs = await conn.fetch("SELECT datname FROM pg_database WHERE datistemplate = false;")
        db_names = [r["datname"] for r in dbs]
        print(f"Databases found: {db_names}")
        await conn.close()
        
        for db in db_names:
            try:
                c = await asyncpg.connect(f"postgresql://postgres:postgres@localhost:5432/{db}")
                tbl_count = await c.fetchval("SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")
                print(f"Database '{db}' is ONLINE - Total tables: {tbl_count}")
                await c.close()
            except Exception as e:
                print(f"Database '{db}' connection error: {e}")
    except Exception as e:
        print(f"PostgreSQL main connection error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
