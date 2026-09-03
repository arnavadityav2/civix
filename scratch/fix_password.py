import psycopg

conn_str = 'postgresql://postgres:CivixPass123%21%40%23@localhost:5433/civix_test'
try:
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute("ALTER ROLE civix_api WITH PASSWORD 'cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'")
        conn.commit()
        print("Password updated successfully.")
except Exception as e:
    print(f'ERROR: {e}')
