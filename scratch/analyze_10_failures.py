import psycopg2
import json

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

with psycopg2.connect(pg_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, entity_id, action, entity_type, seq_no, retry_count, error_status, error_message, payload
            FROM civix.outbox
            WHERE error_status = 'PERMANENT_FAILURE'
        """)
        rows = cur.fetchall()

for r in rows:
    event_id, entity_id, action, entity_type, seq_no, retry_count, error_status, error_message, payload = r
    print(f"--- EVENT {event_id} ---")
    print(f"Entity: {entity_id}")
    print(f"Action: {action}, Type: {entity_type}, Seq: {seq_no}")
    print(f"Retry Count: {retry_count}, Status: {error_status}")
    print(f"Error Message: {error_message}")
    print(f"Payload keys: {list(payload.keys())}")
    # Inspect payload for missing endpoints...
    if action == 'UPSERT_ASSERTION' or action == 'UPSERT_RELATIONSHIP' or action == 'UPSERT_NODE':
        print(f"Payload: {json.dumps(payload)[:200]}...")
