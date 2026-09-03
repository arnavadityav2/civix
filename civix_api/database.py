import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings

# Engine configuration with pooling. We don't set pool checkout events for RLS!
# RLS MUST be established within the transaction lifecycle inside dependencies.py.

pool_size = int(os.getenv("CIVIX_API_POOL_SIZE", "5"))
max_overflow = int(os.getenv("CIVIX_API_MAX_OVERFLOW", "10"))

engine = create_async_engine(
    settings.civix_database_url,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

try:
    from neo4j import AsyncGraphDatabase
    neo4j_driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password)
    )
except ImportError:
    neo4j_driver = None

