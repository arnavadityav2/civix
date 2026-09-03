import psycopg2

def inspect_cases_detail():
    conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    cur.execute("""
        SELECT c.case_id, c.case_number, c.title, c.case_type, count(cer.role) as roles_count
        FROM civix.investigative_case c
        LEFT JOIN civix.case_entity_role cer ON c.case_id = cer.case_id
        GROUP BY c.case_id, c.case_number, c.title, c.case_type
        ORDER BY roles_count DESC
        LIMIT 20;
    """)
    rows = cur.fetchall()

    print("==========================================================")
    print("TOP CASES BY ENTITY ROLE COUNT IN DEMO DATABASE")
    print("==========================================================")
    for cid, cnum, title, ctype, rcnt in rows:
        print(f"ID: {cid} | Type: {ctype:<15} | Roles: {rcnt:<3} | Num: {cnum}")

    conn.close()

if __name__ == "__main__":
    inspect_cases_detail()
