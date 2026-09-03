import asyncio, json
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_idx():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test')
    async with engine.begin() as conn:
        res = await conn.execute(text(
            """SELECT indexname, indexdef
               FROM pg_indexes 
               WHERE schemaname = 'civix' AND tablename = 'source_record'"""
        ))
        print(json.dumps([dict(r) for r in res.mappings()], indent=2))
    await engine.dispose()

asyncio.run(check_idx())
