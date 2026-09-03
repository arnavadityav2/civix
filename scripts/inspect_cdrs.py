import duckdb

con = duckdb.connect(":memory:")
cdrs = con.execute("SELECT caller_person_id, caller_phone_id, callee_phone_id FROM read_parquet('demo_world_15k_output/cdrs/**/*.parquet') LIMIT 5").fetchall()
print("CDR sample:", cdrs)

txns = con.execute("SELECT sender_account_id, receiver_account_id FROM read_parquet('demo_world_15k_output/transactions/**/*.parquet') LIMIT 5").fetchall()
print("Txn sample:", txns)
con.close()
