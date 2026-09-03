import duckdb
import psycopg2
import psycopg2.extras
import time

conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
conn.autocommit = True
cur = conn.cursor()

con = duckdb.connect(":memory:")
sim_rows = con.execute("SELECT sim_id::TEXT, iccid FROM read_parquet('demo_world_15k_output/sims/**/*.parquet')").fetchall()
print(f"Loaded {len(sim_rows)} SIM rows from Parquet.")

# Insert entity rows for SIMs
entity_rows = [(r[0], 'SIM', 'ACTIVE') for r in sim_rows]
t0 = time.time()
psycopg2.extras.execute_values(
    cur,
    "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING",
    entity_rows,
    page_size=5000
)
print(f"Inserted {len(entity_rows)} SIM entity rows in {time.time()-t0:.2f}s")

t0 = time.time()
psycopg2.extras.execute_values(
    cur,
    "INSERT INTO civix.sim (entity_id, iccid) VALUES %s ON CONFLICT DO NOTHING",
    sim_rows,
    page_size=5000
)
print(f"Inserted {len(sim_rows)} SIM rows in {time.time()-t0:.2f}s")

cur.execute("SELECT count(*) FROM civix.sim;")
print("Postgres SIM table count:", cur.fetchone()[0])

dev_rows = con.execute("SELECT device_id::TEXT, imei, 'SMARTPHONE', brand FROM read_parquet('demo_world_15k_output/devices/**/*.parquet')").fetchall()
print(f"\nLoaded {len(dev_rows)} Device rows from Parquet.")

dev_entity_rows = [(r[0], 'DEVICE', 'ACTIVE') for r in dev_rows]
t0 = time.time()
psycopg2.extras.execute_values(
    cur,
    "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING",
    dev_entity_rows,
    page_size=5000
)
print(f"Inserted {len(dev_entity_rows)} Device entity rows in {time.time()-t0:.2f}s")

t0 = time.time()
psycopg2.extras.execute_values(
    cur,
    "INSERT INTO civix.device (entity_id, imei, device_type, manufacturer) VALUES %s ON CONFLICT DO NOTHING",
    dev_rows,
    page_size=5000
)
print(f"Inserted {len(dev_rows)} Device rows in {time.time()-t0:.2f}s")

cur.execute("SELECT count(*) FROM civix.device;")
print("Postgres Device table count:", cur.fetchone()[0])

conn.close()
con.close()
