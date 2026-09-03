import asyncio
from civix_api.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(settings.civix_database_url)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM civix.assertion"))
        print(f'Assertions count: {res.scalar()}')
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
