import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from uuid import uuid4
import os

from civix_api.config import settings

@pytest.mark.asyncio
async def test_case_creation_deferred_fk():
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    user_a_id = uuid4()
    user_b_id = uuid4()
    case_id_1 = uuid4()
    case_num = f"TEST-{uuid4().hex[:8]}"

    try:
        auth_a = f"auth-a-{user_a_id}"
        auth_b = f"auth-b-{user_b_id}"
        uname_a = f"user_a_{uuid4().hex[:8]}"
        uname_b = f"user_b_{uuid4().hex[:8]}"
        # Create users first under postgres or civix_api context, doesn't matter for user creation
        async with TestSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES (:ua, :aa, :una, 'User A', 'INVESTIGATOR'),
                       (:ub, :ab, :unb, 'User B', 'INVESTIGATOR')
                """),
                {"ua": user_a_id, "ub": user_b_id, "aa": auth_a, "ab": auth_b, "una": uname_a, "unb": uname_b}
            )
            await session.commit()
    
        # A. Valid creation test
        async with TestSessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a_id)})
            
            # 2. Insert case_access first
            await session.execute(
                text("""
                INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by)
                VALUES (:cid, :uid, 'ADMIN', :uid)
                """),
                {"cid": case_id_1, "uid": user_a_id}
            )
            
            # 3. Insert investigative_case second
            await session.execute(
                text("""
                INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at)
                VALUES (:cid, :cnum, 'Test Case A', 'CRIMINAL', 'Test Jur', now())
                """),
                {"cid": case_id_1, "cnum": case_num}
            )
            
            # 4. Commit successfully
            await session.commit()
        
        # 5. Retrievable by User A
        async with TestSessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a_id)})
            res = await session.execute(text("SELECT case_number FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id_1})
            assert res.scalar() == case_num
            
        # B. Invalid deferred FK
        async with TestSessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            bad_case_id = uuid4()
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a_id)})
            await session.execute(
                text("""
                INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by)
                VALUES (:cid, :uid, 'ADMIN', :uid)
                """),
                {"cid": bad_case_id, "uid": user_a_id}
            )
            import sqlalchemy.exc
            with pytest.raises(sqlalchemy.exc.IntegrityError) as exc_info:
                await session.commit()
            assert "case_access_case_id_fkey" in str(exc_info.value)

        # C. RLS enforcement remains intact
        async with TestSessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_b_id)})
            res2 = await session.execute(text("SELECT count(*) FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id_1})
            assert res2.scalar() == 0

        # D. Existing RLS policy remains unchanged
        async with TestSessionLocal() as session:
            pol_res = await session.execute(text("SELECT polname, polcmd::text FROM pg_policy WHERE polrelid = 'civix.investigative_case'::regclass"))
            policy = pol_res.first()
            assert policy[0] == 'investigative_case_access_policy'
            assert policy[1] == '*' # All commands

            cls_res = await session.execute(text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE relname = 'investigative_case'"))
            cls = cls_res.first()
            assert cls[0] == True
            assert cls[1] == True

        # E. Application role remains unprivileged
        async with TestSessionLocal() as session:
            role_res = await session.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = 'civix_api'"))
            role = role_res.first()
            assert role[0] == False
            assert role[1] == False

    finally:
        # Cleanup
        async with TestSessionLocal() as session:
            await session.execute(text("SET ROLE civix_api"))
            
            # Delete Case 1 (if created by user_a)
            await session.execute(text("SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"), {"uid": str(user_a_id)})
            await session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id_1})
            await session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_id_1})
            
            # Delete any case_access for user_a and user_b just in case
            await session.execute(text("DELETE FROM civix.case_access WHERE user_id IN (:ua, :ub)"), {"ua": user_a_id, "ub": user_b_id})
            
            # Reset role to clear current_user_id before deleting users
            await session.execute(text("SELECT set_config('civix.current_user_id', '', true), set_config('app.current_user_id', '', true)"))
            await session.execute(text("DELETE FROM civix.civix_user WHERE user_id IN (:ua, :ub)"), {"ua": user_a_id, "ub": user_b_id})
            await session.commit()
        await test_engine.dispose()

