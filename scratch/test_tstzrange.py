import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from datetime import datetime, timezone
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        now = datetime.now(timezone.utc)
        res = await conn.execute(text("SELECT tstzrange(CAST(:ts AS timestamptz), CAST(:ts AS timestamptz), '[]')"), {"ts": now})
        print("tstzrange result:", res.fetchone()[0])

if __name__ == "__main__":
    asyncio.run(main())
