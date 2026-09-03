import psycopg2
conn = psycopg2.connect("postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("SELECT count(*) FROM civix.evidence_artifact WHERE processing_status = 'PENDING' AND created_at > now() - interval '1 hour'")
print("Pending (last hour):", cur.fetchone()[0])
cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
print("Outbox pending:", cur.fetchone()[0])
