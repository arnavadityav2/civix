import duckdb, os

con = duckdb.connect(':memory:')
con.execute("SET memory_limit='6GB'")
try:
    os.makedirs('D:/civix_tmp', exist_ok=True)
    con.execute("SET temp_directory='D:/civix_tmp'")
except: pass

root = 'D:/civix_data/synthetic/profile_v2_v2a'

print('=== SCHEMA AUDIT: profile_v2_v2a ===\n')

def audit_entity(name, path_rel):
    path = root + '/' + path_rel
    if not os.path.isdir(path):
        print(f'{name}: MISSING\n'); return
    parquets = []
    for dp, _, files in os.walk(path):
        for f in files:
            if f.endswith('.parquet'):
                parquets.append(os.path.join(dp, f).replace('\\', '/'))
    if not parquets:
        print(f'{name}: EMPTY\n'); return
    schema = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{parquets[0]}')").df()
    null_sql = ', '.join([f"SUM(CASE WHEN {r} IS NULL THEN 1 ELSE 0 END)*1.0/COUNT(*) AS {r}" for r in schema['column_name']])
    try:
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet({parquets})").fetchone()[0]
    except:
        n = con.execute(f"SELECT COUNT(*) FROM read_parquet('{parquets[0]}')").fetchone()[0]
        n = n * len(parquets)
    print(f'{name}: {n:,} rows, {len(schema)} columns')
    for _, r in schema.iterrows():
        print(f'  {r["column_name"]:45s} {r["column_type"]}')
    print()

audit_entity('PERSONS',     'persons')
audit_entity('CDRS (sample)', 'cdrs')
audit_entity('TRANSACTIONS', 'transactions')
audit_entity('ACCOUNTS',    'accounts')
audit_entity('PHONES',      'phones')
audit_entity('SIMS',        'sims')
audit_entity('DEVICES',     'devices')
audit_entity('CELL SECTORS','cell_sectors')
audit_entity('COMMUNITIES', 'communities')
audit_entity('GROUND TRUTH LABELS', 'ground_truth/person_labels')
audit_entity('SPLITS',      'ground_truth/train_val_test_split')

# Split distribution
sp_path = root + '/ground_truth/train_val_test_split'
parquets = [os.path.join(sp_path, f).replace('\\', '/') for f in os.listdir(sp_path) if f.endswith('.parquet')]
if parquets:
    sc = con.execute(f"SELECT split, COUNT(*) n FROM read_parquet({parquets}) GROUP BY split ORDER BY n DESC").df()
    print('SPLIT DISTRIBUTION:')
    print(sc.to_string(index=False))
    print()

# Timestamp range in CDRs
cdr_path = root + '/cdrs'
parquets = []
for dp, _, files in os.walk(cdr_path):
    for f in files:
        if f.endswith('.parquet'):
            parquets.append(os.path.join(dp, f).replace('\\', '/'))
            if len(parquets) >= 3:
                break
    if len(parquets) >= 3:
        break
if parquets:
    r = con.execute(f"SELECT MIN(start_time) as min_ts, MAX(start_time) as max_ts FROM read_parquet({parquets})").fetchone()
    print(f'CDR TIMESTAMP RANGE (sample 3 shards): {r[0]} to {r[1]}')

# Check if scenario_class is in persons
persons_path = root + '/persons'
pfiles = [os.path.join(persons_path, f).replace('\\', '/') for f in os.listdir(persons_path) if f.endswith('.parquet')]
if pfiles:
    cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{pfiles[0]}')").df()['column_name'].tolist()
    dangerous = [c for c in cols if any(k in c.lower() for k in ['scenario', 'label', 'risk_score', 'positive', 'false_pos'])]
    if dangerous:
        print(f'\n!!! DANGER: Persons table contains label-adjacent columns: {dangerous}')
    else:
        print('\nPersons table: NO label-adjacent columns detected. SAFE.')

con.close()
