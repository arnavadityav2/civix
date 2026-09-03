import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
    res = await conn.fetch("SELECT polname, pg_get_expr(polqual, polrelid) as polqual, pg_get_expr(polwithcheck, polrelid) as polwithcheck FROM pg_policy WHERE polrelid = 'civix.observation'::regclass")
    for r in res:
        print(f"Policy: {r['polname']}")
        print(f"  Qual: {r['polqual']}")
        print(f"  WithCheck: {r['polwithcheck']}")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
