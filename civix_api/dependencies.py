import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import AsyncGenerator

from .database import AsyncSessionLocal
from .auth.principal import AuthenticatedCivixUser
from .auth.jwt import get_user_id_from_token, oauth2_scheme

logger = logging.getLogger(__name__)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a raw, unauthenticated DB session (useful for auth checks)."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user_from_token(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> AuthenticatedCivixUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    user_id = get_user_id_from_token(token.credentials)
    
    # Query user from DB (run as civix_api but before RLS context is established for the endpoint)
    # This is safe because civix_user is not RLS protected in a way that hides identity rows.
    result = await session.execute(
        text("SELECT user_id, username, role, clearance_level FROM civix.civix_user WHERE user_id = :uid"),
        {"uid": user_id}
    )
    user_row = result.first()
    if not user_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return AuthenticatedCivixUser(
        user_id=user_row[0],
        username=user_row[1],
        role=user_row[2],
        clearance_level=user_row[3]
    )

async def get_rls_session(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Acquires an async database session and securely establishes the RLS context
    for the current transaction using a parameterized query.
    
    The identity is strictly request-scoped and transaction-local.
    """
    try:
        # We explicitly establish the transaction-local user identity
        # Set both for backward and forward compatibility with RLS policies
        await session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true), set_config('civix.current_user_id', :uid, true)"),
            {"uid": str(user.user_id)}
        )
        
        # Yield the RLS-configured session to the router
        yield session
        
        # Commit on successful completion of the request
        await session.commit()
    except Exception:
        # Rollback on any failure
        await session.rollback()
        raise

async def get_neo4j_session():
    """Provides an async Neo4j session or None if Neo4j is unavailable."""
    from .database import neo4j_driver
    if not neo4j_driver:
        yield None
        return

    try:
        async with neo4j_driver.session() as session:
            yield session
    except Exception as e:
        logger.error(f"Neo4j session error: {e}")
        raise

