import asyncpg
import asyncio

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    
    rows = await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='investigative_lead'")
    print('Lead columns:', [r['column_name'] for r in rows])
    
    rows2 = await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='assertion'")
    print('Assertion columns:', [r['column_name'] for r in rows2])
    
    await c.close()
asyncio.run(run())
