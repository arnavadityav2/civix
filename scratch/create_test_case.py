"""
CIVIX Round 2A — Create E2E Test Case
Creates a test case + grants ADMIN access to the admin user.
"""
import psycopg
import uuid
from datetime import datetime, timezone

DB_URL = "postgresql://postgres:postgres@localhost:5433/civix_test"
ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"

conn = psycopg.connect(DB_URL)
conn.autocommit = True
cur = conn.cursor()

# Create a Round 2A test case
case_id = uuid.uuid4()
cur.execute("""
    INSERT INTO civix.investigative_case (
        case_id, case_number, title, case_type,
        priority, status, jurisdiction,
        lead_investigator_id, opened_at
    ) VALUES (
        %s, %s, %s,
        'CRIMINAL', 'HIGH', 'ACTIVE',
        'Jaipur, Rajasthan',
        %s, CURRENT_DATE
    )
    ON CONFLICT DO NOTHING
    RETURNING case_id
""", (
    case_id,
    "CIVIX/R2A/2026/001",
    "Round 2A E2E Test Case — Verma Chemical Trading Fraud",
    ADMIN_USER_ID,
))
result = cur.fetchone()
if result is None:
    print(f"Case already exists — trying to find it.")
    cur.execute("SELECT case_id FROM civix.investigative_case WHERE title LIKE '%Round 2A%' LIMIT 1")
    r = cur.fetchone()
    if r:
        case_id = r[0]
    else:
        print("ERROR: Could not create or find test case.")
        conn.close()
        exit(1)
else:
    case_id = result[0]

print(f"Test case ID: {case_id}")

# Grant ADMIN access to our admin user
access_id = uuid.uuid4()
cur.execute("""
    INSERT INTO civix.case_access (
        access_id, case_id, user_id, permission_level,
        granted_by, granted_at, is_revoked
    ) VALUES (
        %s, %s, %s, 'ADMIN',
        %s, %s, false
    )
    ON CONFLICT DO NOTHING
""", (
    access_id,
    case_id,
    ADMIN_USER_ID,
    ADMIN_USER_ID,
    datetime.now(timezone.utc),
))

# Verify access was created
cur.execute("""
    SELECT ca.user_id, ca.permission_level, cu.username
    FROM civix.case_access ca
    JOIN civix.civix_user cu ON cu.user_id = ca.user_id
    WHERE ca.case_id = %s AND ca.is_revoked = false
""", (case_id,))
print(f"\nCase access:")
for r in cur.fetchall():
    print(f"  {r[2]} ({r[0]}) — {r[1]}")

conn.close()

print(f"\n=== E2E TEST CASE READY ===")
print(f"Case ID: {case_id}")
print(f"Admin User ID: {ADMIN_USER_ID}")
