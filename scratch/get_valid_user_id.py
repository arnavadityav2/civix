import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT user_id, username FROM civix.civix_user LIMIT 5"))
        rows = res.fetchall()
        for r in rows:
            print("User:", r[0], r[1])

if __name__ == '__main__':
    asyncio.run(main())
