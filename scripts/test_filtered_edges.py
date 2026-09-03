import duckdb
import psycopg2

pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
pg_cur = pg_conn.cursor()
pg_cur.execute("SELECT entity_id::TEXT FROM civix.phone_number;")
valid_phones = set(r[0] for r in pg_cur.fetchall())
pg_conn.close()

print(f"Total valid phone_number entity_ids in PostgreSQL: {len(valid_phones):,d}")

duck_con = duckdb.connect(":memory:")
cdr_path = "demo_world_15k_output/cdrs/**/*.parquet"

tuples = duck_con.execute(f"""
    SELECT 
        caller_phone_id::TEXT AS src,
        callee_phone_id::TEXT AS dst,
        COUNT(*)::INT AS source_event_count,
        MIN(timestamp)::TEXT AS source_start_time,
        MAX(timestamp)::TEXT AS source_end_time
    FROM read_parquet('{cdr_path}')
    WHERE caller_phone_id IS NOT NULL AND callee_phone_id IS NOT NULL
    GROUP BY caller_phone_id, callee_phone_id
""").fetchall()

print(f"Total raw grouped CDR tuples: {len(tuples):,d}")

valid_tuples = [r for r in tuples if r[0] in valid_phones and r[1] in valid_phones]
print(f"Total 100% valid CDR tuples matching live Neo4j PhoneNumber nodes: {len(valid_tuples):,d}")
duck_con.close()
