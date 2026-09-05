import asyncpg
import asyncio

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    rows = await c.fetch("SELECT entity_type, consumed_at IS NULL as not_consumed, count(*) FROM civix.outbox GROUP BY entity_type, consumed_at IS NULL")
    for r in rows:
        print(dict(r))
    await c.close()

asyncio.run(run())
