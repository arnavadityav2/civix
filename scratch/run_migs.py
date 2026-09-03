import asyncio
import asyncpg
from civix_api.config import settings

async def apply():
    url = 'postgresql://postgres:postgres@localhost:5433/civix_test'
    conn = await asyncpg.connect(url)
    try:
        with open('database/migrations/016_outbox_sequence.sql', 'r') as f:
            m16 = f.read()
        with open('database/migrations/017_outbox_queue.sql', 'r') as f:
            m17 = f.read()
            
        print("Applying 016...")
        await conn.execute(m16)
        print("Applying 017...")
        await conn.execute(m17)
        print("Done!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply())
