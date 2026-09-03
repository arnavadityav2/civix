import asyncio
import asyncpg
import json

DB_URL = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

async def main():
    conn = await asyncpg.connect(DB_URL)
    res = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='entity';")
    print(json.dumps([dict(r) for r in res], indent=2))
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
