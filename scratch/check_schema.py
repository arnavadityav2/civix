import asyncio
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def check_pg():
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='civix'"))
        tables = [row[0] for row in result]
        print('Tables:', tables)
        for table in ['entity', 'person', 'media', 'evidence', 'case_entity_role', 'evidence_media']:
            if table in tables:
                res = await session.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}'"))
                cols = [row[0] for row in res]
                print(f'{table} columns:', cols)

asyncio.run(check_pg())
