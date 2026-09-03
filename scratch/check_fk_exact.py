import asyncio
from uuid import uuid4
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def check():
    async with AsyncSessionLocal() as session:
        user_id = 'd9c9e54a-7bc9-42b4-8ab3-3889025e1975'
        case_id = uuid4()
        access_id = uuid4()

        await session.execute(text("INSERT INTO civix.civix_user (user_id, username, role) VALUES (:uid, 'T-99', 'ADMIN') ON CONFLICT DO NOTHING"), {"uid": user_id})
        
        await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(user_id)})

        try:
            # 1. Insert case_access FIRST
            await session.execute(
                text("""
                    INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
                    VALUES (:aid, :cid, :uid, 'ADMIN', :uid)
                """),
                {
                    "aid": access_id,
                    "cid": case_id,
                    "uid": user_id
                }
            )

            # 2. Insert investigative_case SECOND
            await session.execute(
                text("""
                    INSERT INTO civix.investigative_case (
                        case_id, case_number, title, case_type, priority, jurisdiction, 
                        opened_at
                    )
                    VALUES (
                        :cid, 'TEST-CHK', 'Title', 'CRIMINAL', 'MEDIUM', 'Jur', now()
                    )
                """),
                {
                    "cid": case_id,
                }
            )
            
            print("Successfully inserted both in order!")
        except Exception as e:
            print(f"Exception: {type(e).__name__}: {e}")
        finally:
            await session.rollback()
        
if __name__ == "__main__":
    asyncio.run(check())
