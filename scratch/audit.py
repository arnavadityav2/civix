import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from civix_api.config import settings

async def get_schema():
    engine = create_async_engine(str(settings.civix_database_url))
    async with engine.connect() as conn:
        print("--- source_record indexes ---")
        res = await conn.execute(text("""
            SELECT indexdef FROM pg_indexes WHERE schemaname = 'civix' AND tablename = 'source_record'
        """))
        for row in res: print(row[0])
        
        print("\n--- source_record constraints ---")
        res = await conn.execute(text("""
            SELECT conname, pg_get_constraintdef(c.oid)
            FROM pg_constraint c
            JOIN pg_namespace n ON n.oid = c.connamespace
            WHERE conrelid = 'civix.source_record'::regclass
        """))
        for row in res: print(row)

if __name__ == '__main__':
    asyncio.run(get_schema())
