import psycopg2
conn = psycopg2.connect("postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("SELECT pg_get_functiondef('civix.claim_next_outbox_event()'::regprocedure)")
print(cur.fetchone()[0])
