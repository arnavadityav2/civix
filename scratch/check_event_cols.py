import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = 'investigative_lead'
        """))
        cols = [r[0] for r in res.fetchall()]
        print("investigative_lead columns:", cols)

if __name__ == '__main__':
    asyncio.run(main())
