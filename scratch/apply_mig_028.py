import psycopg2

PG_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"

def apply_migration():
    with open("database/migrations/028_c2_candidate_provenance.sql", "r") as f:
        sql = f.read()
        
    with psycopg2.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()
            print("Migration 028 applied successfully")

if __name__ == "__main__":
    apply_migration()
