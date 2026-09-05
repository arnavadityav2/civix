import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath("."))
from sqlalchemy import text
from civix_api.database import engine

async def main():
    async with engine.connect() as conn:
        entity_ids = ['9674dbb9-0c1e-759a-e8ea-412bbb24d1ce', '856662f4-4e01-dfba-e683-cd319f4f425e', '00a90c69-0c15-f7b9-0830-00da19ffaab9']
        for eid in entity_ids:
            res_ident = await conn.execute(text("""
                SELECT identifier_type, raw_identifier
                FROM civix.source_identity
                WHERE entity_id = CAST(:eid AS uuid);
            """), {"eid": eid})
            rows = res_ident.fetchall()
            print(f"Entity {eid}: {rows}")

if __name__ == "__main__":
    asyncio.run(main())
