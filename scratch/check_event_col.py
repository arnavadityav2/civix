import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='event'"))
        for r in res.fetchall():
            print(f"Column: {r[0]}, Type: {r[1]}, UDT: {r[2]}")

if __name__ == "__main__":
    asyncio.run(main())
