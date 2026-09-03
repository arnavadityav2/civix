import asyncio
import asyncpg
import os

async def main():
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="civix_test"
    )
    rows = await conn.fetch("SELECT case_id, case_number, title, jurisdiction FROM civix.case;")
    print("PostgreSQL Cases:")
    for r in rows:
        print(dict(r))
    await conn.close()

asyncio.run(main())
