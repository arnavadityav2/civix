import asyncio
import asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    rows = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='outbox'")
    print("Columns in outbox:", [r['column_name'] for r in rows])
    await conn.close()
asyncio.run(main())
