"""
Diagnose and fix the Round 2A test case issue.
The case_access row exists (b281ad86) but the case is invisible.
This means the investigative_case row either:
  1. Was never actually inserted (commit failed silently), OR
  2. Was inserted but is invisible due to RLS policy requiring opened_by = current user
"""
import psycopg2

ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"
CASE_ID = "b281ad86-1b43-458c-b751-fc44cb467823"

conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'
)
cur = conn.cursor()

# Check current RLS policies on investigative_case
cur.execute("""
    SELECT polname, polcmd, pg_get_expr(polqual, polrelid) as qual,
           pg_get_expr(polwithcheck, polrelid) as withcheck
    FROM pg_policy
    WHERE polrelid = 'civix.investigative_case'::regclass
    ORDER BY polname
""")
policies = cur.fetchall()
print("=== RLS policies on investigative_case ===")
for p in policies:
    print(f"  {p[0]} ({p[1]}): QUAL={p[2][:100] if p[2] else 'NULL'} | CHECK={p[3][:100] if p[3] else 'NULL'}")

# Try setting RLS and checking the case
cur.execute("SELECT set_config('app.current_user_id', %s, false)", (ADMIN_USER_ID,))
cur.execute("SELECT set_config('civix.current_user_id', %s, false)", (ADMIN_USER_ID,))
cur.execute("SELECT case_id, title, opened_by FROM civix.investigative_case WHERE case_id = %s", (CASE_ID,))
row = cur.fetchone()
print(f"\n=== Case {CASE_ID} (with RLS set_config false=session-local) ===")
print(f"  Result: {row}")

# Count total cases visible to this user
cur.execute("SELECT COUNT(*) FROM civix.investigative_case")
print(f"  Total visible cases: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\nDone.")
