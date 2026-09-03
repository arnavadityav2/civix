import duckdb

con = duckdb.connect(":memory:")
sim_df = con.execute("SELECT * FROM read_parquet('demo_world_15k_output/sims/**/*.parquet')").df()
print("SIM Parquet total rows:", len(sim_df))
print("SIM Unique sim_ids:", sim_df['sim_id'].nunique())
print("SIM Duplicate sim_ids:", len(sim_df) - sim_df['sim_id'].nunique())

if len(sim_df) - sim_df['sim_id'].nunique() > 0:
    dupes = sim_df[sim_df.duplicated('sim_id', keep=False)]
    print("\nSample SIM duplicates:")
    print(dupes.head(10))

dev_df = con.execute("SELECT * FROM read_parquet('demo_world_15k_output/devices/**/*.parquet')").df()
print("\nDevice Parquet total rows:", len(dev_df))
print("Device Unique device_ids:", dev_df['device_id'].nunique())
print("Device Duplicate device_ids:", len(dev_df) - dev_df['device_id'].nunique())

if len(dev_df) - dev_df['dev_id' if 'dev_id' in dev_df else 'device_id'].nunique() > 0:
    dupes_dev = dev_df[dev_df.duplicated('device_id', keep=False)]
    print("\nSample Device duplicates:")
    print(dupes_dev.head(10))
