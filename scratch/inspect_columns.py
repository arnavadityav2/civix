import asyncio
import asyncpg

async def inspect():
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
    tables = await conn.fetch("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'civix'
    """)
    for t in tables:
        tname = t['table_name']
        cols = await conn.fetch("""
            SELECT column_name, data_type FROM information_schema.columns 
            WHERE table_schema = 'civix' AND table_name = $1
        """, tname)
        col_list = [f"{c['column_name']} ({c['data_type']})" for c in cols]
        print(f"TABLE civix.{tname}: {', '.join(col_list)}\n")
    await conn.close()

asyncio.run(inspect())
