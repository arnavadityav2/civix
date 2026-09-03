"""
CIVIX 2.0 — Round 2A Test Prerequisite Setup
Creates the test investigative_case and verifies case_access for admin user.
Run before e2e_test_round2a.py.
"""
import psycopg2
import uuid

ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"

conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'
)
cur = conn.cursor()

# Set RLS context so INSERT is allowed
cur.execute("SELECT set_config('app.current_user_id', %s, true), "
            "set_config('civix.current_user_id', %s, true)", 
            (ADMIN_USER_ID, ADMIN_USER_ID))

# Check if Round 2A test case already exists
cur.execute("SELECT case_id, title FROM civix.investigative_case WHERE title ILIKE '%Round 2A%' LIMIT 1")
row = cur.fetchone()

if row:
    case_id = str(row[0])
    print(f"Test case already exists: {case_id} — {row[1]}")
else:
    case_id = str(uuid.uuid4())
    cur.execute("""
        INSERT INTO civix.investigative_case (
            case_id, title, case_type, jurisdiction,
            status, opened_by, classification_level
        ) VALUES (
            %s, 'CIVIX Round 2A E2E Test Case', 'FRAUD',
            'Rajasthan, India', 'ACTIVE', %s, 'UNCLASSIFIED'
        )
    """, (case_id, ADMIN_USER_ID))
    print(f"Created test case: {case_id}")

# Ensure case_access for admin user
cur.execute("""
    SELECT permission_level FROM civix.case_access
    WHERE case_id = %s AND user_id = %s AND is_revoked = false
""", (case_id, ADMIN_USER_ID))
access = cur.fetchone()

if access:
    print(f"Admin access already exists: {access[0]}")
else:
    cur.execute("""
        INSERT INTO civix.case_access (case_id, user_id, permission_level, is_revoked)
        VALUES (%s, %s, 'ADMIN', false)
        ON CONFLICT DO NOTHING
    """, (case_id, ADMIN_USER_ID))
    print("Granted ADMIN access to test case")

conn.commit()
cur.close()
conn.close()
print(f"\nSUCCESS. Test case ID: {case_id}")
print("You can now run: python scratch/e2e_test_round2a.py")
