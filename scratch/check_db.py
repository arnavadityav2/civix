import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, dbname='civix_test', user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx')
cur = conn.cursor()
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'outbox'")
print("COLUMNS civix.outbox:", cur.fetchall())
