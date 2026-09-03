import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_drift():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test')
    async with engine.begin() as conn:
        # Get tables
        tables = await conn.execute(text(
            "SELECT relname FROM pg_class JOIN pg_namespace ON pg_class.relnamespace = pg_namespace.oid WHERE pg_namespace.nspname = 'civix' AND relkind = 'r' ORDER BY relname"
        ))
        db_tables = [r[0] for r in tables.fetchall()]
        print("DB Tables:", db_tables)
    await engine.dispose()

asyncio.run(check_drift())
