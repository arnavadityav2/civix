import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()

cur.execute("""
    SELECT u.user_id, u.username, u.role, array_agg(ca.case_id::text) as accessible_cases
    FROM civix.civix_user u
    LEFT JOIN civix.case_access ca ON u.user_id = ca.user_id AND ca.is_revoked = FALSE
    GROUP BY u.user_id, u.username, u.role
    HAVING count(ca.case_id) > 0
    LIMIT 10;
""")

print("==========================================================")
print("USER CASE ACCESS IN POSTGRESQL")
print("==========================================================")
for row in cur.fetchall():
    print(f"User: {row[1]} ({row[2]}) | Cases Count: {len(row[3])} | Cases: {row[3][:3]}...")

conn.close()
