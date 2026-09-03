import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from civix_api.main import app
from civix_api.database import engine, AsyncSessionLocal

from sqlalchemy import text
from uuid import uuid4
import sys

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from civix_api.dependencies import get_db_session, get_rls_session
from civix_api.config import settings

# Create a dedicated test engine with NullPool to avoid teardown GC issues
test_engine = create_async_engine(settings.civix_database_url, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)

@pytest.fixture(scope="session", autouse=True)
async def cleanup_db_engine():
    yield
    await test_engine.dispose()

@pytest.fixture(scope="session", autouse=True)
def override_dependencies():
    async def override_get_db_session():
        async with TestSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db_session] = override_get_db_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def create_test_user():
    created_users = []
    
    async def _create(username=None, role="INVESTIGATOR"):
        if username is None:
            username = f"user_{uuid4().hex[:8]}"
        user_id = uuid4()
        auth_id = f"auth-{user_id}"
        async with TestSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, is_active)
                VALUES (:uid, :auth, :uname, :uname, :role, true)
                """),
                {"uid": user_id, "auth": auth_id, "uname": username, "role": role}
            )
            await session.commit()
        created_users.append(user_id)
        return user_id
        
    yield _create
    
    # Teardown

    
    async with TestSessionLocal() as session:
        for uid in created_users:
            # Must assume the user's role to bypass RLS for deletion
            await session.execute(text("SELECT set_config('app.current_user_id', :uid, true)"), {"uid": str(uid)})
            
            # Delete leads, tasks, and evidence to prevent FK violations
            await session.execute(text(
                "DELETE FROM civix.investigative_lead WHERE case_id IN (SELECT case_id FROM civix.case_access WHERE user_id = :uid) "
                "AND case_id NOT IN (SELECT case_id FROM civix.hypothesis)"
            ), {"uid": uid})
            await session.execute(text(
                "DELETE FROM civix.case_entity_role WHERE case_id IN (SELECT case_id FROM civix.case_access WHERE user_id = :uid) "
                "AND case_id NOT IN (SELECT case_id FROM civix.hypothesis)"
            ), {"uid": uid})
            await session.execute(text(
                "DELETE FROM civix.evidence_instance WHERE case_id IN (SELECT case_id FROM civix.case_access WHERE user_id = :uid) "
                "AND case_id NOT IN (SELECT case_id FROM civix.hypothesis)"
            ), {"uid": uid})
            
            # Delete mutable entities safely. Skip cases that have hypotheses since hypotheses are immutable and block case deletion.
            await session.execute(text(
                "DELETE FROM civix.investigative_case WHERE case_id IN (SELECT case_id FROM civix.case_access WHERE user_id = :uid) "
                "AND case_id NOT IN (SELECT case_id FROM civix.hypothesis)"
            ), {"uid": uid})

            await session.execute(text(
                "DELETE FROM civix.case_access WHERE user_id = :uid AND case_id NOT IN (SELECT case_id FROM civix.hypothesis)"
            ), {"uid": uid})
            
            # Reset role
            await session.execute(text("SELECT set_config('app.current_user_id', '', true)"))
            
            # Note: We do NOT delete civix.entity, civix.person, or civix.case_entity_role 
            # because they are immutable. This means civix_user also cannot be deleted due to FKs.
            # We leave them in the test database.
            
        await session.commit()
