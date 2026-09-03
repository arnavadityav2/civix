import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="civix_test"
    )
    rows = await conn.fetch("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog', 'information_schema');")
    print("PostgreSQL Tables:")
    for r in rows:
        print(r['table_schema'], '.', r['table_name'])
    await conn.close()

asyncio.run(main())
