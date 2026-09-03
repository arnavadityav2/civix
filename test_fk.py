import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from civix_api.config import settings

async def check():
    engine = create_async_engine(settings.civix_database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            WHERE conrelid = 'civix.case_access'::regclass AND contype = 'f'
        """))
        for r in res:
            print(r)

asyncio.run(check())
