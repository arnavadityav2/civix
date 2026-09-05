import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))
from civix_api.database import engine
from sqlalchemy import text

async def main():
    async with engine.connect() as conn:
        r = await conn.execute(text("SELECT COUNT(*) FROM civix.person"))
        total_people = r.scalar()
        print(f"Total people in database: {total_people}")

asyncio.run(main())
