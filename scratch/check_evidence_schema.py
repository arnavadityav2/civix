import asyncpg
import asyncio

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    rows = await c.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='evidence_artifact'")
    print('Artifact:')
    for r in rows:
        print(dict(r))
    rows = await c.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='evidence_instance'")
    print('Instance:')
    for r in rows:
        print(dict(r))
    await c.close()

asyncio.run(run())
