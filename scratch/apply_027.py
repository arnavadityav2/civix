import psycopg2

conn = psycopg2.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
conn.autocommit = True
with conn.cursor() as cur:
    with open("database/migrations/027_c1_dlq.sql", "r") as f:
        cur.execute(f.read())
print("Migration 027 applied successfully.")
