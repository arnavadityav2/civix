import psycopg
import json

dsn = "postgresql://postgres:postgres@localhost:5432/civix_demo"
conn = psycopg.connect(dsn)
cur = conn.cursor()

# Get FKs
cur.execute("""
    SELECT
        kcu.table_name,
        kcu.column_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
    WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='civix';
""")
fks = cur.fetchall()

# Get Indexes
cur.execute("""
    SELECT tablename, indexname, indexdef
    FROM pg_indexes
    WHERE schemaname = 'civix'
    ORDER BY tablename, indexname;
""")
indexes = cur.fetchall()

# Get RLS status
cur.execute("""
    SELECT relname, relrowsecurity, relforcerowsecurity
    FROM pg_class c
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE n.nspname = 'civix' AND c.relkind = 'r';
""")
rls_info = cur.fetchall()

with open("scratch/db_fks_and_indexes.json", "w") as f:
    json.dump({
        "fks": fks,
        "indexes": indexes,
        "rls": rls_info
    }, f, indent=2)

print("Saved FKs and indexes to scratch/db_fks_and_indexes.json")
