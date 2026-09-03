"""
Apply migration 029 using the postgres superuser via psql-equivalent execution.
Reads the whole file and splits by proper SQL statement boundaries.
"""
import asyncio
import asyncpg
import sys

DB_CONFIGS = [
    "postgresql://postgres:postgres@localhost:5433/civix_test",
    "postgresql://postgres:@localhost:5433/civix_test",
]

SQL_FILE = "database/migrations/029_c3_intelligence_engine.sql"


async def apply(dsn: str):
    print(f"Connecting to: {dsn.split('@')[-1]}")
    conn = await asyncpg.connect(dsn, server_settings={'search_path': 'civix,public'})
    try:
        with open(SQL_FILE, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Execute the entire migration as one script via execute()
        # asyncpg.Connection.execute() can handle multi-statement scripts
        # when submitted as a single string to the simple query protocol
        print("Applying full migration as single script...")
        await conn.execute(sql)
        print("Migration applied successfully!")
        
        # Verify
        col_count = await conn.fetchval("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = 'civix'
              AND table_name = 'investigative_lead'
              AND column_name IN ('feature_vector_version','deterministic_findings',
                                  'explanation','explanation_status')
        """)
        tbl_exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'civix' AND table_name = 'investigative_finding'
            )
        """)
        print(f"\nVerification:")
        print(f"  New columns on investigative_lead: {col_count}/4")
        print(f"  investigative_finding table exists: {tbl_exists}")
        if col_count == 4 and tbl_exists:
            print("  PASS: Migration 029 verified.")
        else:
            print(f"  FAIL: col_count={col_count}, tbl_exists={tbl_exists}")
            sys.exit(1)
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
    print(f"\nAll connection attempts failed. Last error: {last_err}")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
