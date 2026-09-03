import asyncio
from uuid import uuid4
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        user_id = uuid4()
        auth = f"auth-{user_id}"
        await session.execute(
            text("INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role) VALUES (:uid, :auth, :uname, :uname, 'INVESTIGATOR')"),
            {"uid": user_id, "auth": auth, "uname": f"user_{user_id}"}
        )
        await session.commit()
        
        # Start a new transaction by executing something
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_id)}
        )
        
        # Check current setting
        res = await session.execute(text("SELECT current_setting('app.current_user_id', TRUE)"))
        print(f"Current setting: {res.scalar()}")
        
        res = await session.execute(text("SELECT user_id, role, is_active FROM civix.civix_user WHERE user_id = :uid"), {"uid": user_id})
        print(f"User check: {res.fetchall()}")
        
        try:
            case_id = uuid4()
            await session.execute(
                text("INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction) VALUES (:cid, 'CIV-999', 'Test Case', 'FINANCIAL', 'Delhi')"),
                {"cid": case_id}
            )
            print("INSERT case succeeded")
        except Exception as e:
            print(f"INSERT case failed: {type(e).__name__} - {e}")

if __name__ == "__main__":
    asyncio.run(check())
