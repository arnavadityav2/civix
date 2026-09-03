import os
import psycopg2
from civix_api.worker.cdc import CDCWorker
import logging

logging.basicConfig(level=logging.INFO)

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

# Run worker briefly to process existing events
worker = CDCWorker(pg_dsn, "bolt://localhost:7687", "neo4j", "password")

processed = 0
failures = 0
try:
    while True:
        if worker.process_next_event():
            processed += 1
        else:
            break
except Exception as e:
    logging.error(f"Worker crashed: {e}")

# Check results
with psycopg2.connect(pg_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
        still_pending = cur.fetchone()[0]
        cur.execute("SELECT error_status, count(*) FROM civix.outbox WHERE error_status IS NOT NULL GROUP BY error_status")
        errors = cur.fetchall()

print(f"Processed loop {processed} times.")
print(f"Still pending: {still_pending}")
print(f"Errors: {errors}")
