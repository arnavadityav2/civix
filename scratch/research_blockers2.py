import asyncio
import asyncpg
import json

DB_DSN = 'postgresql://postgres:postgres@localhost:5433/civix_test'

async def research_blockers():
    conn = await asyncpg.connect(DB_DSN)
    
    print("=== COLUMNS of investigative_finding ===")
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='investigative_finding'")
    print([r['column_name'] for r in cols])
    
    print("\n=== COLUMNS of assertion ===")
    cols = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='assertion'")
    print([r['column_name'] for r in cols])

    await conn.close()

asyncio.run(research_blockers())
