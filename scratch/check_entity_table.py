import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='civix' AND table_name LIKE '%entity%'"))
        print("Entity tables:", [r[0] for r in res.fetchall()])

if __name__ == "__main__":
    asyncio.run(main())
