import psycopg2
import uuid

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT user_id FROM civix.civix_user WHERE role = 'ADMIN' LIMIT 1;")
admin_uid = cur.fetchone()[0]

case_id = str(uuid.uuid4())
access_id = str(uuid.uuid4())

try:
    print("Testing insert into case_access FIRST...")
    cur.execute("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (%s, %s, %s, 'ADMIN', %s);
    """, (access_id, case_id, admin_uid, admin_uid))
    conn.commit()
    print("Success case_access first")
except Exception as e:
    conn.rollback()
    print(f"FAILED case_access first: {e}")

try:
    print("\nTesting insert into investigative_case FIRST...")
    cur.execute("""
        INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, priority, jurisdiction, opened_at, lead_investigator_id)
        VALUES (%s, 'TEST-ORDER-001', 'Test Order Title', 'CRIMINAL', 'MEDIUM', 'DELHI', NOW(), %s);
    """, (case_id, admin_uid))
    
    cur.execute("""
        INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
        VALUES (%s, %s, %s, 'ADMIN', %s);
    """, (access_id, case_id, admin_uid, admin_uid))
    conn.commit()
    print("SUCCESS: investigative_case first!")
except Exception as e:
    conn.rollback()
    print(f"FAILED investigative_case first: {e}")

conn.close()
