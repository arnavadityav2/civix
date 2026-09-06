import duckdb
import psycopg2

duck_con = duckdb.connect(":memory:")

print("Inspecting Parquet CDR sample values:")
res = duck_con.execute("""
    SELECT caller_person_id::text, caller_phone_id::text, callee_phone_id::text, timestamp, duration_seconds, call_type
    FROM read_parquet('demo_world_15k_output/cdrs/**/*.parquet')
    WHERE caller_person_id IS NOT NULL
    LIMIT 10;
""").fetchall()

for r in res:
    print(r)

print("\nChecking if caller_phone_id exists in civix.phone_number DB table:")
phone_ids = [r[1] for r in res]
pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
pg_cur = pg_conn.cursor()

pg_cur.execute("SELECT entity_id::text, msisdn, operator FROM civix.phone_number WHERE entity_id::text = ANY(%s);", (phone_ids,))
matched_phones = pg_cur.fetchall()
print("Matched phone_number rows in DB:", matched_phones)

# Check if there are phone_number entries for Suresh Valmiki or any person in civix.person
pg_cur.execute("""
    SELECT p.display_name, pn.entity_id::text, pn.msisdn, pn.operator
    FROM civix.phone_number pn
    JOIN civix.person p ON pn.entity_id = p.entity_id
    LIMIT 20;
""")
print("\nPersons with Phone Numbers in DB:")
for r in pg_cur.fetchall():
    print(f"  - {r[0]}: MSISDN {r[2]} ({r[3]}), Entity ID: {r[1]}")

pg_conn.close()
duck_con.close()
