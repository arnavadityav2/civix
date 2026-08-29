import duckdb, os

con = duckdb.connect(':memory:')
root = 'D:/civix_data/synthetic/profile_v2_v2a'

# CDR timestamp range
cdr_path = root + '/cdrs'
parquets = []
for dp, _, files in os.walk(cdr_path):
    for f in files:
        if f.endswith('.parquet'):
            parquets.append(os.path.join(dp, f).replace('\\', '/'))
            break
    if parquets:
        break

pq0 = parquets[0]
r = con.execute(f"SELECT MIN(\"timestamp\") as min_ts, MAX(\"timestamp\") as max_ts FROM read_parquet('{pq0}')").fetchone()
print(f'CDR timestamp range (1 shard): {r[0]} to {r[1]}')

txn_path = root + '/transactions'
parquets_txn = []
for dp, _, files in os.walk(txn_path):
    for f in files:
        if f.endswith('.parquet'):
            parquets_txn.append(os.path.join(dp, f).replace('\\', '/'))
            break
    if parquets_txn:
        break

pq1 = parquets_txn[0]
r2 = con.execute(f"SELECT MIN(\"timestamp\") as a, MAX(\"timestamp\") as b FROM read_parquet('{pq1}')").fetchone()
print(f'TXN timestamp range (1 shard): {r2[0]} to {r2[1]}')

sp_path = root + '/ground_truth/train_val_test_split'
sfiles = [os.path.join(sp_path, f).replace('\\', '/') for f in os.listdir(sp_path) if f.endswith('.parquet')]
cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{sfiles[0]}')").df()['column_name'].tolist()
print(f'SPLITS table columns: {cols}')
scenario_in_splits = 'scenario_class' in cols
print(f'WARNING - scenario_class in splits: {scenario_in_splits} (leakage risk if joined naively)')

fv1 = root + '/features_v1'
print(f'\nfeatures_v1 dir exists: {os.path.isdir(fv1)}')
if os.path.isdir(fv1):
    ff = os.listdir(fv1)
    print(f'  Files: {ff}')

gt_path = root + '/ground_truth/person_labels'
gfiles = [os.path.join(gt_path, f).replace('\\', '/') for f in os.listdir(gt_path) if f.endswith('.parquet')]

adv = con.execute(f"SELECT is_hard_negative, is_low_visibility, in_criminal_network, COUNT(*) n FROM read_parquet({gfiles}) GROUP BY 1,2,3 ORDER BY n DESC LIMIT 12").df()
print('\nAdversarial group distribution (ground truth):')
print(adv.to_string(index=False))

diff = con.execute(f"SELECT difficulty, COUNT(*) n FROM read_parquet({gfiles}) GROUP BY difficulty ORDER BY n DESC").df()
print('\nDifficulty distribution:')
print(diff.to_string(index=False))

# Financial pattern distribution  
r3 = con.execute(f"SELECT financial_pattern, COUNT(*) n FROM read_parquet('{pq1}') GROUP BY financial_pattern ORDER BY n DESC").df()
print('\nFinancial pattern distribution (1 shard):')
print(r3.to_string(index=False))

con.close()
