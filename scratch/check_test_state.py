"""Check Round 2A test case and outbox table."""
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, dbname='civix_test',
                        user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx')
cur = conn.cursor()

print("=== Round 2A test cases ===")
cur.execute("SELECT case_id, title FROM civix.investigative_case WHERE title ILIKE '%round%' LIMIT 5")
print(cur.fetchall())

print("\n=== All outbox-related tables ===")
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'civix' AND table_name ILIKE '%outbox%' ORDER BY table_name")
print([r[0] for r in cur.fetchall()])

print("\n=== Admin user ===")
cur.execute("SELECT user_id, username, role FROM civix.civix_user WHERE user_id = '3c3ba8b7-7f44-401d-a0ac-4c4747650883'")
print(cur.fetchall())

print("\n=== civix_user count ===")
cur.execute("SELECT COUNT(*) FROM civix.civix_user")
print(cur.fetchone()[0])

print("\n=== investigative_case count ===")
cur.execute("SELECT COUNT(*) FROM civix.investigative_case")
print(cur.fetchone()[0])

print("\n=== outbox_event count ===")
try:
    cur.execute("SELECT COUNT(*) FROM civix.outbox_event")
    print("outbox_event:", cur.fetchone()[0])
except Exception as e:
    print(f"Error: {e}")
    conn.rollback()

cur.close()
conn.close()
print("Done.")
