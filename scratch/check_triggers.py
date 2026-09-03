"""Check triggers on evidence_artifact table."""
import psycopg2
conn = psycopg2.connect(host='localhost', port=5433, dbname='civix_test', user='postgres', password='postgres')
cur = conn.cursor()
cur.execute("SELECT tgname, pg_get_triggerdef(oid) FROM pg_trigger WHERE tgrelid = 'civix.evidence_artifact'::regclass")
for r in cur.fetchall():
    print(r)
cur.close()
conn.close()
