import asyncio
import sys
sys.path.insert(0, '.')
from sqlalchemy import text
from civix_api.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as session:
        r = await session.execute(
            text("SELECT case_id, role::text FROM civix.case_entity_role WHERE entity_id = '263f32c4-30fd-40a8-b01b-6def1b47e90c'")
        )
        print("Roles for 263f32c4-30fd-40a8-b01b-6def1b47e90c:")
        for row in r.fetchall():
            print(" ", row[0], row[1])

if __name__ == '__main__':
    asyncio.run(main())
