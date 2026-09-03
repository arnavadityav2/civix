import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from uuid import uuid4

async def test_failure_mode():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:CivixPass123%21%40%23@localhost:5433/civix_test",
        pool_size=1, max_overflow=0
    )
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    user_id = uuid4()
    case_id = uuid4()
    
    async with SessionLocal() as session:
        await session.execute(
            text("""
            INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
            VALUES (:uid, :auth, 'failuser', 'Fail User', 'INVESTIGATOR')
            """),
            {"uid": user_id, "auth": f"fail-{user_id}"}
        )
        await session.commit()
        
    try:
        async with SessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(user_id)})
            
            print("Attempting to insert case_access first (with NOT DEFERRABLE FK)...")
            try:
                await session.execute(
                    text("""
                    INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by)
                    VALUES (:cid, :uid, 'ADMIN', :uid)
                    """),
                    {"cid": case_id, "uid": user_id}
                )
                print("SUCCESS (Unexpected if NOT DEFERRABLE)")
            except Exception as e:
                print(f"FAILED as expected: {type(e).__name__} - {str(e)}")
                await session.rollback()
                
            print("\nAttempting to insert investigative_case first (with FORCE RLS)...")
            try:
                await session.execute(
                    text("""
                    INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at)
                    VALUES (:cid, 'TEST-FAIL', 'Fail Case', 'CRIMINAL', 'Jur', now())
                    """),
                    {"cid": case_id}
                )
                print("SUCCESS (Unexpected if RLS prevents it)")
            except Exception as e:
                print(f"FAILED as expected: {type(e).__name__} - {str(e)}")
                await session.rollback()

    finally:
        async with SessionLocal() as session:
            await session.execute(text("RESET ROLE"))
            await session.execute(text("DELETE FROM civix.civix_user WHERE user_id = :uid"), {"uid": user_id})
            await session.commit()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_failure_mode())
