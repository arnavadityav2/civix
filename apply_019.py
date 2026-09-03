import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user="postgres", password="postgres", host="localhost", port=5433, database="civix_test")
    await conn.execute("ALTER TABLE civix.assertion ADD COLUMN IF NOT EXISTS authorized_case_ids UUID[] NOT NULL DEFAULT '{}';")
    await conn.execute("ALTER TABLE civix.hypothesis_support ADD COLUMN IF NOT EXISTS tx_end TIMESTAMPTZ NULL;")
    with open("database/migrations/019_outbox_epistemic_and_edge_triggers.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    await conn.execute(sql)
    await conn.close()
    print("Migration applied!")

if __name__ == "__main__":
    asyncio.run(main())
