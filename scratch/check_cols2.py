import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/civix")
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'investigative_lead'"))
        cols = [r[0] for r in res.fetchall()]
        print("investigative_lead cols:", cols)

asyncio.run(main())
