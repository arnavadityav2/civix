import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT DISTINCT c.case_id::text, c.case_number, c.title FROM civix.investigative_case c JOIN civix.event_location el ON c.case_id = el.case_id;")
rows = cur.fetchall()
print("Cases with spatial events:")
for r in rows:
    print(f"  - {r[0]} | {r[1]} | {r[2]}")
conn.close()
