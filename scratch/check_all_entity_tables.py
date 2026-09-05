import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='civix'"))
        all_tables = [r[0] for r in res.fetchall()]
        print("All CIVIX tables:", all_tables)

        for tbl in all_tables:
            res_cols = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='{tbl}' AND column_name = 'entity_id'"))
            if res_cols.fetchall():
                res_count = await conn.execute(text(f"SELECT COUNT(*) FROM civix.{tbl}"))
                cnt = res_count.fetchone()[0]
                print(f"  Table '{tbl}' has entity_id! Row count: {cnt}")

if __name__ == "__main__":
    asyncio.run(main())
