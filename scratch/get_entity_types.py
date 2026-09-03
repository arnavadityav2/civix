import psycopg2
import json

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

with psycopg2.connect(pg_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT id, payload->>'subject_entity_type', payload->>'object_entity_type' FROM civix.outbox WHERE error_status = 'PERMANENT_FAILURE'")
        rows = cur.fetchall()
        print(json.dumps(rows, indent=2))
