import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT c.case_id, c.case_number, c.title, c.opened_at, c.created_at FROM civix.investigative_case c JOIN civix.event_location el ON c.case_id = el.case_id GROUP BY c.case_id ORDER BY c.created_at DESC;")
rows = cur.fetchall()
print(f"Total spatial cases in DB: {len(rows)}")
for r in rows:
    print(f"  - [{r[1]}] {r[2]:<60} | opened_at: {r[3]} | created_at: {r[4]}")
conn.close()
