"""Apply migration 024 via asyncpg directly (bypasses SQLAlchemy bind-param parsing)."""
import asyncio
import asyncpg
import os

DB_URL = os.getenv(
    "CIVIX_DATABASE_URL_ASYNCPG",
    "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
)

with open("database/migrations/024_case_entity_role_projection.sql", "r", encoding="utf-8") as f:
    sql = f.read()

async def main():
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute(sql)
        print("Migration 024 applied successfully.")
    finally:
        await conn.close()

asyncio.run(main())
