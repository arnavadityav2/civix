import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect(user="postgres", password="postgres", host="localhost", port=5433, database="civix_test")
    with open("database/migrations/023_fix_f01_f02_invariants.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    await conn.execute(sql)
    await conn.close()
    print("Migration applied!")

if __name__ == "__main__":
    asyncio.run(main())

