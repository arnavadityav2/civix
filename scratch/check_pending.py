import psycopg2
conn = psycopg2.connect("postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test")
cur = conn.cursor()
cur.execute("SELECT processing_status, count(*) FROM civix.evidence_artifact GROUP BY processing_status")
print("Artifacts:", cur.fetchall())
cur.execute("SELECT status, count(*) FROM civix.outbox GROUP BY status")
print("Outbox:", cur.fetchall())
