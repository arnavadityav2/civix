"""Check cases as superuser to bypass RLS."""
import psycopg2

# Try to connect as superuser or with broader permissions
# The civix_api user can't see cases without RLS set
conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'
)
cur = conn.cursor()

# Set RLS context first
cur.execute("SELECT set_config('app.current_user_id', '3c3ba8b7-7f44-401d-a0ac-4c4747650883', true)")

# Now query
cur.execute("SELECT case_id, title FROM civix.investigative_case ORDER BY created_at DESC LIMIT 5")
rows = cur.fetchall()
print("Cases (with RLS context):", rows)

# Check case_access
cur.execute("SELECT case_id, user_id, permission_level FROM civix.case_access WHERE user_id = '3c3ba8b7-7f44-401d-a0ac-4c4747650883' LIMIT 5")
access = cur.fetchall()
print("Case access:", access)

cur.close()
conn.close()
print("Done.")
