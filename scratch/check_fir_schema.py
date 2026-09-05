import asyncpg
import asyncio

async def run():
    c = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/civix_demo')
    
    rows = await c.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='fir'")
    print('FIR columns:', [r['column_name'] for r in rows])
    
    await c.close()
asyncio.run(run())
