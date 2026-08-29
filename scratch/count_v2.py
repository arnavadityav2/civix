import duckdb, os

con = duckdb.connect(':memory:')

datasets = {
    'profile_v2_dev (5K dev run)':   'D:/civix_data/synthetic/profile_v2_dev',
    'profile_v2_v2a (integration 1)': 'D:/civix_data/synthetic/profile_v2_v2a',
    'profile_v2_v2b (integration 2)': 'D:/civix_data/synthetic/profile_v2_v2b',
    'profile_v2_v2c (integration 3)': 'D:/civix_data/synthetic/profile_v2_v2c',
    'profile_v2_int (int run)':       'D:/civix_data/synthetic/profile_v2_int',
}

for name, root in datasets.items():
    print(f'\n=== {name} ===')
    for entity in ['persons', 'cdrs', 'transactions', 'accounts', 'phones', 'devices', 'sims']:
        folder = os.path.join(root, entity)
        if os.path.isdir(folder):
            parquets = []
            for dirpath, _, files in os.walk(folder):
                parquets += [os.path.join(dirpath, f).replace('\\', '/') for f in files if f.endswith('.parquet')]
            if parquets:
                globs = "', '".join(parquets[:5])
                try:
                    n = con.execute(f"SELECT COUNT(*) FROM read_parquet(['{globs}'])").fetchone()[0]
                    total = n * (len(parquets) // 5 + 1) if len(parquets) > 5 else n
                    actual = con.execute(f"SELECT COUNT(*) FROM read_parquet({parquets})").fetchone()[0]
                    print(f'  {entity}: {actual:,}')
                except Exception as e:
                    print(f'  {entity}: ERROR - {e}')
            else:
                print(f'  {entity}: (empty)')
        else:
            print(f'  {entity}: (no dir)')

# Check ground truth
print('\n=== Ground Truth Labels ===')
for name, root in datasets.items():
    gt_path = os.path.join(root, 'ground_truth', 'person_labels')
    if os.path.isdir(gt_path):
        parquets = [os.path.join(gt_path, f).replace('\\', '/') for f in os.listdir(gt_path) if f.endswith('.parquet')]
        if parquets:
            try:
                df = con.execute(f"SELECT scenario_class, COUNT(*) as n FROM read_parquet({parquets}) GROUP BY scenario_class ORDER BY n DESC").df()
                print(f'\n  {name}:')
                print(df.to_string(index=False))
            except Exception as e:
                print(f'  {name}: ERROR - {e}')

con.close()
