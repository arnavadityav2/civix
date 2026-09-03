import psycopg2

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

def fetch_constraint():
    with psycopg2.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT conname, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE conname = 'chk_assertion_has_assertor' OR conname = 'chk_assertion_source'
            """)
            for row in cur.fetchall():
                print(row)

if __name__ == "__main__":
    fetch_constraint()
