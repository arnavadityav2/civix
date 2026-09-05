import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        for tbl in ["person", "phone_number", "financial_account", "organization", "vehicle"]:
            res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='{tbl}'"))
            cols = [r[0] for r in res.fetchall()]
            print(f"Table {tbl}: {cols}")
            
            # Query sample row
            res_sample = await conn.execute(text(f"SELECT * FROM civix.{tbl} LIMIT 1"))
            row = res_sample.fetchone()
            if row:
                print(f"  Sample {tbl}: {dict(row._mapping)}")

if __name__ == "__main__":
    asyncio.run(main())
