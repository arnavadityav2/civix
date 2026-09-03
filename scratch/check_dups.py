import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from civix_api.config import settings

async def check_duplicates():
    engine = create_async_engine(str(settings.civix_database_url))
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT source_id, external_reference, count(*) 
            FROM civix.source_record 
            GROUP BY source_id, external_reference 
            HAVING count(*) > 1
        """))
        rows = res.fetchall()
        print(f'Duplicate groups found: {len(rows)}')
        for r in rows: print(r)

if __name__ == '__main__':
    asyncio.run(check_duplicates())
