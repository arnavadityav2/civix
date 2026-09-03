import psycopg2
conn = psycopg2.connect("postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname='bitemporal_insert'")
print(cur.fetchone()[0])
cur.execute("SELECT pg_get_functiondef(oid) FROM pg_proc WHERE proname='outbox_event_trigger'")
print(cur.fetchone()[0])
