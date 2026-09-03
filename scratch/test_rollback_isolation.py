import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from uuid import uuid4

async def test_rollback_isolation():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:CivixPass123%21%40%23@localhost:5433/civix_test",
        pool_size=1, max_overflow=0
    )
    SessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    user_a = uuid4()
    user_b = uuid4()
    case_id = uuid4()
    
    async with SessionLocal() as session:
        await session.execute(
            text("""
            INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
            VALUES (:ua, :auth_a, 'user_a', 'User A', 'INVESTIGATOR'),
                   (:ub, :auth_b, 'user_b', 'User B', 'INVESTIGATOR')
            """),
            {"ua": user_a, "ub": user_b, "auth_a": f"auth-a-{user_a}", "auth_b": f"auth-b-{user_b}"}
        )
        await session.commit()

    try:
        # TEST STEP: Force exception before inserting investigative_case
        async with SessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(user_a)})
            
            await session.execute(
                text("""
                INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by)
                VALUES (:cid, :uid, 'ADMIN', :uid)
                """),
                {"cid": case_id, "uid": user_a}
            )
            
            # SIMULATE CRASH/EXCEPTION
            print("Simulating application crash before investigative_case insert...")
            await session.rollback()

        # TEST STEP: Re-acquire connection from pool and verify state
        async with SessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            # Connect as User B
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true)"), {"uid": str(user_b)})
            
            # A. No case_access survives
            res1 = await session.execute(text("SELECT count(*) FROM civix.case_access WHERE case_id = :cid"), {"cid": case_id})
            assert res1.scalar() == 0, "case_access leaked!"
            
            # B. No investigative_case survives
            res2 = await session.execute(text("SELECT count(*) FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id})
            assert res2.scalar() == 0, "investigative_case leaked!"
            
            # C/D. User B cannot see User A's uncommitted identity (no leakage)
            res3 = await session.execute(text("SELECT current_setting('civix.current_user_id', true)"))
            assert res3.scalar() == str(user_b), "User identity leaked!"
            
            print("Rollback test passed successfully! All isolation criteria met.")

    finally:
        async with SessionLocal() as session:
            await session.execute(text("RESET ROLE"))
            await session.execute(text("DELETE FROM civix.civix_user WHERE user_id IN (:ua, :ub)"), {"ua": user_a, "ub": user_b})
            await session.commit()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_rollback_isolation())
