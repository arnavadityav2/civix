import duckdb

con = duckdb.connect()

entities = ['phones', 'sims', 'devices', 'accounts', 'cell_sectors']

for e in entities:
    print(f"\n--- {e} ---")
    df = con.execute(f"DESCRIBE SELECT * FROM read_parquet('D:/civix_data/synthetic/profile_v2_v2a/{e}/*.parquet')").df()
    print(df[['column_name', 'column_type']])
