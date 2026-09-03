"""Check tables with block_mutation_trigger."""
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, dbname='civix_test', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT tgrelid::regclass FROM pg_trigger WHERE tgname = 'block_mutation_trigger'")
for r in cur.fetchall():
    print(r[0])
cur.close()
conn.close()
