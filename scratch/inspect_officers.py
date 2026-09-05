import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("POSTGRES_DB", "civix_demo")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASS,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
case_id = cur.fetchone()[0]

print("=== 1. case_access officers ===")
cur.execute("""
    SELECT ca.access_id, ca.user_id, ca.permission_level, u.username, u.display_name, u.role, u.department
    FROM civix.case_access ca
    JOIN civix.civix_user u ON ca.user_id = u.user_id
    WHERE ca.case_id = %s
""", (case_id,))
print(cur.fetchall())

print("\n=== 2. FIR filed_by user ===")
cur.execute("""
    SELECT f.fir_number, f.filed_by, u.username, u.display_name, u.department
    FROM civix.fir f
    LEFT JOIN civix.civix_user u ON f.filed_by = u.user_id
    WHERE f.case_id = %s
""", (case_id,))
print(cur.fetchall())

print("\n=== 3. Lead Investigator ===")
cur.execute("""
    SELECT c.lead_investigator_id, u.username, u.display_name, u.role, u.department
    FROM civix.investigative_case c
    LEFT JOIN civix.civix_user u ON c.lead_investigator_id = u.user_id
    WHERE c.case_id = %s
""", (case_id,))
print(cur.fetchall())

print("\n=== 4. All civix_users in DB ===")
cur.execute("SELECT user_id, username, display_name, role, clearance_level, department FROM civix.civix_user")
print(cur.fetchall())

print("\n=== 5. Check if OFFICER_IN_CHARGE or officer roles exist in case_entity_role anywhere ===")
cur.execute("""
    SELECT cer.role, COUNT(*)
    FROM civix.case_entity_role cer
    WHERE cer.role::text LIKE '%OFFICER%'
    GROUP BY cer.role
""")
print(cur.fetchall())

cur.close()
conn.close()
