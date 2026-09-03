import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test")
    
    async with engine.begin() as conn:
        print("Applying migration 022...")
        await conn.execute(text("CREATE UNIQUE INDEX idx_source_record_idempotency ON civix.source_record (source_id, external_reference) WHERE external_reference IS NOT NULL"))
                
    print("Migration 022 applied successfully!")

asyncio.run(main())
