import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user="postgres", password="postgres", host="localhost", port=5433, database="civix_test")
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='assertion'")
    print([c['column_name'] for c in cols])
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
