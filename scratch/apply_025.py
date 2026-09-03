import psycopg

with open(r"database\migrations\025_processing_status.sql", "r") as f:
    sql = f.read()

conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute(sql)
    print("Migration 025 applied successfully.")
except Exception as e:
    print(f"ERROR: {e}")
finally:
    # Verify columns
    cur.execute("""
        SELECT column_name, data_type, column_default, is_nullable
        FROM information_schema.columns
        WHERE table_schema = 'civix' AND table_name = 'evidence_artifact'
        ORDER BY ordinal_position
    """)
    print("\nevidence_artifact columns:")
    for r in cur.fetchall():
        print(f"  {r[0]} ({r[1]}, default={r[2]}, nullable={r[3]})")
    conn.close()
