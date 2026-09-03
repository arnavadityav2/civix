import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from civix_api.config import settings

async def test_rls():
    engine = create_async_engine(settings.civix_database_url)
    async with engine.begin() as conn:
        # Create a test user
        user_id = "00000000-0000-0000-0000-000000000001"
        auth_id = "test-auth-1"
        await conn.execute(text("""
            INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, is_active)
            VALUES (:uid, :auth, 'rls_test', 'RLS Test', 'INVESTIGATOR', true)
            ON CONFLICT DO NOTHING
        """), {"uid": user_id, "auth": auth_id})
        
        # Set config (BOTH)
        await conn.execute(text("SELECT set_config('app.current_user_id', :uid, true), set_config('civix.current_user_id', :uid, true)"), {"uid": user_id})
        
        case_id = "00000000-0000-0000-0000-000000000002"
        access_id = "00000000-0000-0000-0000-000000000005"
        
        # INSERT CASE ACCESS FIRST
        try:
            await conn.execute(text("""
                INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
                VALUES (:aid, :cid, :uid, 'ADMIN', :uid)
            """), {"aid": access_id, "cid": case_id, "uid": user_id})
            print("INSERT CASE ACCESS SUCCESS")
        except Exception as e:
            print(f"INSERT CASE ACCESS FAILED: {e}")
            
        # Try to insert case
        try:
            await conn.execute(text("""
                INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction)
                VALUES (:cid, 'TEST-123', 'Test Case', 'CRIMINAL', 'Test')
            """), {"cid": case_id})
            print("INSERT CASE SUCCESS")
        except Exception as e:
            print(f"INSERT CASE FAILED: {e}")

asyncio.run(test_rls())
