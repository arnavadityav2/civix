import asyncio
import asyncpg
import os

# Connect to the DB from .env: postgresql+asyncpg://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test
DB_URL = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

async def main():
    try:
        conn = await asyncpg.connect(DB_URL)
        print("=== SCHEMA INSPECTION ===")
        # Check if visibility_status exists
        res = await conn.fetch("""
            SELECT column_name, data_type, column_default, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'civix' AND table_name = 'entity' AND column_name = 'visibility_status';
        """)
        if res:
            print(f"Column exists: {dict(res[0])}")
        else:
            print("Column does NOT exist.")

        # Check existing values
        print("\n=== EXISTING VALUES ===")
        if res:
            val_counts = await conn.fetch("""
                SELECT visibility_status, count(*) as cnt
                FROM civix.entity
                GROUP BY visibility_status;
            """)
            for row in val_counts:
                print(f"{row['visibility_status']}: {row['cnt']}")
        
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
