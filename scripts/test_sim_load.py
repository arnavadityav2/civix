import duckdb
import psycopg2

con = duckdb.connect(":memory:")
con.execute("INSTALL postgres; LOAD postgres;")
con.execute("ATTACH 'dbname=civix_demo user=postgres password=postgres host=localhost' AS pgres (TYPE postgres);")

print("Sim count in DB before:", con.execute("SELECT COUNT(*) FROM pgres.civix.sim").fetchone()[0])
print("Sim entity count in DB before:", con.execute("SELECT COUNT(*) FROM pgres.civix.entity WHERE entity_type='SIM'").fetchone()[0])

pq_sim = "demo_world_15k_output/sims/*.parquet"
try:
    con.execute(f"""
        INSERT INTO pgres.civix.sim (entity_id, iccid)
        SELECT sim_id::UUID, iccid FROM read_parquet('{pq_sim}');
    """)
except Exception as e:
    print("Exact SIM insert error:", e)

print("Sim count in DB after:", con.execute("SELECT COUNT(*) FROM pgres.civix.sim").fetchone()[0])

print("\nDevice count in DB before:", con.execute("SELECT COUNT(*) FROM pgres.civix.device").fetchone()[0])

pq_dev = "demo_world_15k_output/devices/*.parquet"
con.execute(f"""
    INSERT INTO pgres.civix.device (entity_id, imei, device_type, manufacturer)
    SELECT device_id::UUID, imei, 'SMARTPHONE', brand FROM read_parquet('{pq_dev}') ON CONFLICT DO NOTHING;
""")

print("Device count in DB after:", con.execute("SELECT COUNT(*) FROM pgres.civix.device").fetchone()[0])
