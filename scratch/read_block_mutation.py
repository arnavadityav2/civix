"""Read block_mutation function."""
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, dbname='civix_test', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT prosrc FROM pg_proc WHERE proname = 'block_mutation'")
for r in cur.fetchall():
    print(r[0])
cur.close()
conn.close()
