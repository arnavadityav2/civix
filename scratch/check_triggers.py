import asyncpg
import asyncio 

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    rows = await c.fetch("SELECT tgname, relname FROM pg_trigger JOIN pg_class ON pg_trigger.tgrelid = pg_class.oid WHERE tgname LIKE '%outbox%'")
    for r in rows:
        print(dict(r))
    await c.close()

asyncio.run(run())
