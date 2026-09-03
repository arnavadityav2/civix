import psycopg2

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
cur = conn.cursor()

for table in ["location", "event", "event_location", "investigative_case"]:
    cur.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='civix' AND table_name='{table}';")
    cols = cur.fetchall()
    print(f"--- Table civix.{table} ---")
    for c in cols:
        print(f"  {c[0]:<25} : {c[1]}")

conn.close()
