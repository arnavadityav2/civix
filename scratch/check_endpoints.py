import psycopg2
pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

with psycopg2.connect(pg_dsn) as conn:
    with conn.cursor() as cur:
        # Check one specific endpoint from the first failed event
        cur.execute("SELECT id, action, entity_type, seq_no, consumed_at, error_status FROM civix.outbox WHERE entity_id = '57bed008-c646-4c21-9ea1-b8b43a80068a'")
        print("Endpoint 1 (Subject):", cur.fetchall())
        
        cur.execute("SELECT id, action, entity_type, seq_no, consumed_at, error_status FROM civix.outbox WHERE entity_id = 'c1022c3c-e4dc-4244-9da4-b477653049eb'")
        print("Endpoint 2 (Object):", cur.fetchall())
