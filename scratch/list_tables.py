import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='civix';")
    tbl_names = [t['table_name'] for t in tables]
    print("Tables in civix schema:", sorted(tbl_names))
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
