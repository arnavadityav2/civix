import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        for tbl in ["evidence_instance", "source_record", "assertion", "investigative_lead", "event_participant"]:
            res = await conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='{tbl}'"))
            cols = [r[0] for r in res.fetchall()]
            print(f"Table {tbl}: {cols}")

if __name__ == "__main__":
    asyncio.run(main())
