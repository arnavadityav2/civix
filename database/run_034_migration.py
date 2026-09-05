import psycopg2

sql = """
SET search_path TO civix, public;

ALTER TABLE civix.person ADD COLUMN IF NOT EXISTS avatar_url TEXT NULL;
"""

print("Running migration 034...")
try:
    conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5432/civix_demo")
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    print("Migration 034 successful.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
