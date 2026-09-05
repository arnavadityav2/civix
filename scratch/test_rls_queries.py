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

# Get case_id for CIV-2012-001
cur.execute("SELECT case_id FROM civix.investigative_case WHERE case_number = 'CIV-2012-001'")
case_id = cur.fetchone()[0]

# Check RLS policies on civix tables
cur.execute("""
    SELECT tablename, rowsecurity 
    FROM pg_tables 
    WHERE schemaname = 'civix'
""")
tables = cur.fetchall()
print("=== RLS STATUS PER TABLE ===")
for t, rls in tables:
    if rls:
        print(f"Table {t} HAS RLS ENABLED")

# Test query as normal user vs superuser/app session
# Let's set app context user
cur.execute("SET LOCAL civix.current_user_id = '00000000-0000-0000-0000-000000000001'")
cur.execute("SET LOCAL civix.current_user_role = 'ADMIN'")

cur.execute("""
    SELECT 
        cer.role_id,
        cer.entity_id,
        cer.role,
        cer.role_basis,
        e.entity_type::text as entity_type,
        COALESCE(
            p.display_name,
            o.legal_name,
            v.license_plate,
            d.imei,
            pn.phone_number,
            cer.entity_id::text
        ) as display_name,
        p.gender::text,
        p.date_of_birth,
        p.nationality
    FROM civix.case_entity_role cer
    JOIN civix.entity e ON cer.entity_id = e.entity_id
    LEFT JOIN civix.person p ON e.entity_id = p.entity_id
    LEFT JOIN civix.organization o ON e.entity_id = o.entity_id
    LEFT JOIN civix.vehicle v ON e.entity_id = v.entity_id
    LEFT JOIN civix.device d ON e.entity_id = d.entity_id
    LEFT JOIN civix.phone_number pn ON e.entity_id = pn.entity_id
    WHERE cer.case_id = %s;
""", (case_id,))

rows = cur.fetchall()
print(f"Entities returned under RLS context: {len(rows)}")
for r in rows:
    print(r)

cur.close()
conn.close()
