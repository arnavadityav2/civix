import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="postgres",
        database="civix_test"
    )
    rows = await conn.fetch("SELECT count(*) as total, count(*) FILTER (WHERE consumed_at IS NULL) as unconsumed FROM civix.outbox;")
    print("Outbox stats:", dict(rows[0]))
    await conn.close()

asyncio.run(main())
