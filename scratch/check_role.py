import asyncio
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        res = await session.execute(text("SELECT rolbypasserls FROM pg_roles WHERE rolname = 'civix_api'"))
        print(f"civix_api BYPASSRLS: {res.fetchall()}")
        
        # Check if RLS is bypassed by default for civix_api?
        res = await session.execute(text("SHOW row_security"))
        print(f"row_security: {res.fetchall()}")

if __name__ == "__main__":
    asyncio.run(check())
