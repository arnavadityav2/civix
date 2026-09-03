import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5433/civix_test")
    
    with open("database/migrations/021_adr033_entity_tombstone.sql", "r") as f:
        sql = f.read()

    async with engine.begin() as conn:
        for statement in sql.split(";"):
            statement = statement.strip()
            if statement:
                print("Executing:", statement[:50])
                await conn.execute(text(statement))
                
    print("Migration applied!")

if __name__ == "__main__":
    asyncio.run(main())
