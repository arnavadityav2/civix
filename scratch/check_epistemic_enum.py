import psycopg2
conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()
cur.execute("SELECT enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'epistemic_status_enum' ORDER BY enumlabel")
print("epistemic_status_enum values:", [r[0] for r in cur.fetchall()])
conn.close()
