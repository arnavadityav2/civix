import psycopg2
conn = psycopg2.connect('postgresql://postgres:postgres@localhost:5433/civix_test')
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='outbox'")
print([r[0] for r in cur.fetchall()])
