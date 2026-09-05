import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "scripts"))
from hero_protection import build_hero_world_snapshot

DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/civix_demo"

async def main():
    engine = create_async_engine(DB_URL)
    async with engine.connect() as conn:
        snapshot = await build_hero_world_snapshot(conn)
        print("Hero SHA:", snapshot["overall_hash"])
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
