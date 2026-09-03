import asyncio
import asyncpg
import sys

DB_CONFIGS = [
    "postgresql://postgres:postgres@localhost:5433/civix_test",
    "postgresql://postgres:@localhost:5433/civix_test",
]

SQL_FILE = "database/migrations/030_cctv_subsystem.sql"

async def apply(dsn: str):
    print(f"Connecting to: {dsn.split('@')[-1]}")
    conn = await asyncpg.connect(dsn, server_settings={'search_path': 'civix,public'})
    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print("Applying full migration as single script...")
        await conn.execute(sql)
        print("Migration applied successfully!")
        
    finally:
        await conn.close()


async def main():
    last_err = None
    for dsn in DB_CONFIGS:
        try:
            await apply(dsn)
            return
        except asyncpg.InvalidPasswordError as e:
            print(f"  Auth failed: {e}")
            last_err = e
        except asyncpg.InvalidCatalogNameError as e:
            print(f"  DB not found: {e}")
            last_err = e
        except Exception as e:
            last_err = e
            print(f"  Error with {dsn.split('@')[-1]}: {type(e).__name__}: {e}")
            raise e
    print(f"\nAll connection attempts failed. Last error: {last_err}")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
