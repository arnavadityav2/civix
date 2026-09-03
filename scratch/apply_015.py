import asyncio
import asyncpg
from civix_api.config import settings

async def apply_015():
    # Let's connect as postgres
    url = "postgresql://postgres:CivixPass123!@#@localhost:5433/civix_test"
    conn = await asyncpg.connect(url)

    print(f"Connected as {conn.get_settings().session_authorization}")
    
    with open("database/migrations/015_outbox_node_triggers.sql", "r", encoding="utf-8") as f:
        sql = f.read()

    # Apply the SQL using a transaction block
    async with conn.transaction():
        await conn.execute(sql)
        
    await conn.close()
    print("Migration 015 applied successfully!")

if __name__ == "__main__":
    asyncio.run(apply_015())
