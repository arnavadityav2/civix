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

cur.execute("SET LOCAL civix.current_user_id = '00000000-0000-0000-0000-000000000001'")
cur.execute("SET LOCAL civix.current_user_role = 'ADMIN'")

query = """
    SELECT 
        cer.role_id::text,
        cer.entity_id::text,
        cer.role::text,
        cer.role_basis,
        e.entity_type::text as entity_type,
        COALESCE(
            p.display_name,
            o.legal_name,
            v.registration_number,
            d.imei,
            pn.msisdn,
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
    WHERE cer.case_id = %s

    UNION ALL

    SELECT 
        ca.access_id::text as role_id,
        u.user_id::text as entity_id,
        CASE WHEN c.lead_investigator_id = u.user_id THEN 'INVESTIGATING_OFFICER' ELSE 'OFFICER_IN_CHARGE' END as role,
        COALESCE(c.investigating_unit, 'Assigned Officer') as role_basis,
        'PERSON' as entity_type,
        u.display_name,
        NULL as gender,
        NULL as date_of_birth,
        'IND' as nationality
    FROM civix.case_access ca
    JOIN civix.civix_user u ON ca.user_id = u.user_id
    JOIN civix.investigative_case c ON c.case_id = ca.case_id
    WHERE ca.case_id = %s AND u.user_id != '00000000-0000-0000-0000-000000000001'
"""

cur.execute(query, (case_id, case_id))
rows = cur.fetchall()
print(f"Total entities + officers returned ({len(rows)}):")
for r in rows:
    print(r)

cur.close()
conn.close()
