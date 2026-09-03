import psycopg

db_url = 'postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test'

try:
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT current_user")
            user = cur.fetchone()[0]
            print(f"civix_api direct connection: PASS")
            print(f"Actual connected role: {user}")
except Exception as e:
    print(f'civix_api direct connection: FAIL ({e})')
