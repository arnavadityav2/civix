import asyncio
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT conname, condeferrable, condeferred FROM pg_constraint WHERE conrelid = 'civix.case_access'::regclass"))
        print(f"Constraints: {res.fetchall()}")
        
if __name__ == "__main__":
    asyncio.run(check())
