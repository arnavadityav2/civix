"""Fix: create case properly using session-level set_config."""
import psycopg2
import uuid

ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"

conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'
)
cur = conn.cursor()

# Use false (session-scoped) for the diagnostic connection
cur.execute("SELECT set_config('app.current_user_id', %s, false)", (ADMIN_USER_ID,))
cur.execute("SELECT set_config('civix.current_user_id', %s, false)", (ADMIN_USER_ID,))

# Check all existing cases
cur.execute("SELECT case_id, title FROM civix.investigative_case ORDER BY created_at DESC LIMIT 10")
cases = cur.fetchall()
print("Existing cases:", cases)

# Check case_access
cur.execute("SELECT case_id FROM civix.case_access WHERE user_id = %s", (ADMIN_USER_ID,))
access_cases = [r[0] for r in cur.fetchall()]
print("case_access case_ids:", access_cases)

# The case that has case_access but may not exist in investigative_case
for cid in access_cases:
    cur.execute("SELECT case_id, title FROM civix.investigative_case WHERE case_id = %s", (cid,))
    r = cur.fetchone()
    if r:
        print(f"Case FOUND: {r}")
    else:
        print(f"Case MISSING for case_id={cid}")

# Create the test case fresh
print("\n=== Creating Round 2A test case ===")
new_case_id = uuid.uuid4()
try:
    cur.execute("""
        INSERT INTO civix.investigative_case (
            case_id, title, case_type, jurisdiction, status, classification_level
        ) VALUES (
            %s, 'CIVIX Round 2A E2E Test Case', 'FRAUD',
            'Rajasthan, India', 'ACTIVE', 'UNCLASSIFIED'
        )
    """, (new_case_id,))
    
    # Grant access
    cur.execute("""
        INSERT INTO civix.case_access (case_id, user_id, permission_level, is_revoked)
        VALUES (%s, %s, 'ADMIN', false)
        ON CONFLICT DO NOTHING
    """, (new_case_id, ADMIN_USER_ID))
    
    conn.commit()
    
    # Verify
    cur.execute("SELECT set_config('app.current_user_id', %s, false)", (ADMIN_USER_ID,))
    cur.execute("SELECT case_id, title FROM civix.investigative_case WHERE case_id = %s", (new_case_id,))
    row = cur.fetchone()
    print(f"Created and visible: {row}")
    print(f"\nSUCCESS. Test case ID: {new_case_id}")
    
except Exception as e:
    conn.rollback()
    print(f"ERROR: {e}")

cur.close()
conn.close()
