import psycopg

dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

with psycopg.connect(dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("UPDATE civix.outbox SET consumed_at = NOW() WHERE consumed_at IS NULL")
        conn.commit()
        print(f"Cleared {cur.rowcount} stuck events.")
