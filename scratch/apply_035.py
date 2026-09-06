import psycopg2
import sys

# Apply to civix_test
conn = psycopg2.connect(dbname="civix_test", user="postgres", password="postgres", host="localhost", port=5432)
conn.autocommit = True
cur = conn.cursor()

with open(r"database/migrations/035_investigator_assertion_lifecycle.sql", "r", encoding="utf-8") as f:
    sql = f.read()

try:
    cur.execute(sql)
    print("Migration 035 applied to civix_test successfully.")
    cur.execute("SELECT COUNT(*) FROM civix.assertion")
    count = cur.fetchone()[0]
    print(f"civix_test assertions preserved: {count}")
    conn.close()
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    conn.close()
    sys.exit(1)
