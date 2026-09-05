import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='investigative_case';")
    print([c['column_name'] for c in cols])
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
