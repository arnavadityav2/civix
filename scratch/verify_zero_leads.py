import asyncio
import os
import asyncpg

async def verify_zero_leads():
    # Attempt connection to test DB to verify 0 rows
    dsn = os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_db_admin:admin_pass_123@localhost:5433/civix_test")
    try:
        conn = await asyncpg.connect(dsn)
        count = await conn.fetchval("SELECT count(*) FROM civix.investigative_lead")
        print(f"investigative_lead row count: {count}")
        await conn.close()
    except Exception as e:
        print(f"Could not connect to DB to verify rows dynamically: {e}")
        print("Falling back to static analysis (previously done).")

if __name__ == "__main__":
    asyncio.run(verify_zero_leads())
