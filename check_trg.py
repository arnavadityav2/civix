import asyncio, asyncpg, json
from civix_api.config import settings

async def check():
    db_url = settings.civix_database_url.replace('postgresql+asyncpg', 'postgresql')
    conn = await asyncpg.connect(db_url)
    res = await conn.fetch("SELECT tgname FROM pg_trigger WHERE tgname LIKE 'trg_%_upsert_outbox'")
    print("Triggers:", [r['tgname'] for r in res])
    await conn.close()

asyncio.run(check())
