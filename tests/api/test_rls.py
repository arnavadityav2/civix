import pytest
import uuid
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from httpx import AsyncClient, ASGITransport

from civix_api.main import app
from civix_api.config import settings
from civix_api.dependencies import get_db_session, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.dependencies import get_current_user_from_token
# Add a test endpoint
@app.get("/test/rls")
async def verify_rls_endpoint(
    session: AsyncSession = Depends(get_rls_session),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token)
):
    # Retrieve the current RLS context from Postgres
    result = await session.execute(text("SELECT current_setting('app.current_user_id', true)"))
    current_setting = result.scalar()
    
    # Try to select from a table using RLS to prove access
    # We will use case_entity_role as it has FORCE ROW LEVEL SECURITY.
    await session.execute(text("SELECT count(*) FROM civix.case_entity_role"))
    
    return {"current_user_id": current_setting, "requested_user_id": str(user.user_id)}

@app.get("/test/rls/error")
async def verify_rls_error_endpoint(
    session: AsyncSession = Depends(get_rls_session),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token)
):
    # Retrieve the current RLS context from Postgres
    result = await session.execute(text("SELECT current_setting('app.current_user_id', true)"))
    current_setting = result.scalar()
    
    # Intentionally raise an exception to trigger a rollback in the dependency
    raise HTTPException(status_code=500, detail=f"Intentional Error for user {current_setting}")

@pytest.mark.asyncio
async def test_pool_leakage():
    # Force a small pool for testing leakage. Create inside the test so it binds to the current loop.
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    try:
        # Setup: Insert test users
        async with TestSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES 
                (:id_a, 'test_a', 'test_a', 'Test A', 'INVESTIGATOR'),
                (:id_b, 'test_b', 'test_b', 'Test B', 'INVESTIGATOR')
                """),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
            
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # We override the auth dependency to return User A
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_a_id, username="test_a", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User A
            response_a = await client.get("/test/rls")
            assert response_a.status_code == 200
            data_a = response_a.json()
            assert data_a["current_user_id"] == str(user_a_id)
            
            # Now override auth to return User B
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_b_id, username="test_b", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User B
            response_b = await client.get("/test/rls")
            assert response_b.status_code == 200
            data_b = response_b.json()
            assert data_b["current_user_id"] == str(user_b_id)
            
            # Ensure B did not inherit A's identity from the pool
            assert data_b["current_user_id"] != str(user_a_id)

    finally:
        # Cleanup overrides
        app.dependency_overrides.pop(get_current_user_from_token, None)
        
        # Cleanup DB
        async with TestSessionLocal() as session:
            await session.execute(
                text("DELETE FROM civix.civix_user WHERE user_id IN (:id_a, :id_b)"),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
            
        await test_engine.dispose()

@pytest.mark.asyncio
async def test_pool_leakage_on_rollback():
    """
    Tests that if a request crashes and rolls back, the RLS context is correctly cleared
    and does not leak to the next pooled connection.
    """
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    try:
        # Setup: Insert test users
        async with TestSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES 
                (:id_a, 'test_a', 'test_a', 'Test A', 'INVESTIGATOR'),
                (:id_b, 'test_b', 'test_b', 'Test B', 'INVESTIGATOR')
                """),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
            
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Override auth to return User A
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_a_id, username="test_a", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User A hits the error endpoint
            response_a = await client.get("/test/rls/error")
            assert response_a.status_code == 500
            
            # Now override auth to return User B
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_b_id, username="test_b", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User B on normal endpoint
            response_b = await client.get("/test/rls")
            assert response_b.status_code == 200
            data_b = response_b.json()
            assert data_b["current_user_id"] == str(user_b_id)
            
            # Ensure B did not inherit A's identity from the pool
            assert data_b["current_user_id"] != str(user_a_id)

    finally:
        # Cleanup overrides
        app.dependency_overrides.pop(get_current_user_from_token, None)
        
        # Cleanup DB
        async with TestSessionLocal() as session:
            await session.execute(
                text("DELETE FROM civix.civix_user WHERE user_id IN (:id_a, :id_b)"),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
        
        await test_engine.dispose()

@pytest.mark.asyncio
async def test_runtime_negative_permissions():
    """
    Proves that the civix_api role is actively denied UPDATE/DELETE at runtime,
    independent of any application-level logic.
    """
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    from sqlalchemy.exc import ProgrammingError

    async with TestSessionLocal() as session:
        await session.execute(text("SET ROLE civix_api"))
        
        # 1. audit_event UPDATE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("UPDATE civix.audit_event SET metadata = '{}' WHERE audit_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 2. audit_event DELETE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("DELETE FROM civix.audit_event WHERE audit_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 3. evidence_artifact UPDATE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("UPDATE civix.evidence_artifact SET original_filename = 'tampered' WHERE artifact_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 4. evidence_artifact DELETE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("DELETE FROM civix.evidence_artifact WHERE artifact_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()
        
        # 5. provenance UPDATE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("UPDATE civix.provenance SET derivation_method = 'tampered' WHERE provenance_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 6. provenance DELETE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("DELETE FROM civix.provenance WHERE provenance_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

    await test_engine.dispose()
