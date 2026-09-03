import asyncio
import asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    rows = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema='civix'")
    print("Tables:", [r['table_name'] for r in rows])
    await conn.close()
asyncio.run(main())
