import asyncio
import asyncpg
async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    c = await conn.fetchval("SELECT count(*) FROM civix.person")
    print('Total persons:', c)
    c2 = await conn.fetchval("SELECT count(*) FROM civix.person WHERE generation_run_id IS NOT NULL")
    print('Generated persons:', c2)
    await conn.close()
asyncio.run(main())
