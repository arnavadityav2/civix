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
    rows = await conn.fetch("SELECT * FROM civix.case_access;")
    print("PostgreSQL Case Access List:")
    for r in rows:
        print(dict(r))
    await conn.close()

asyncio.run(main())
