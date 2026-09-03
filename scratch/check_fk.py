import asyncio
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        # Check current user in postgres
        res = await session.execute(text("SELECT current_user, session_user"))
        print(f"User: {res.fetchall()}")
        
        try:
            await session.execute(text("INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES (gen_random_uuid(), 'd9c9e54a-7bc9-42b4-8ab3-3889025e1975', 'ADMIN', 'd9c9e54a-7bc9-42b4-8ab3-3889025e1975')"))
            print("FK not enforced or deferred!")
        except Exception as e:
            print(f"Exception: {e}")
        
if __name__ == "__main__":
    asyncio.run(check())
