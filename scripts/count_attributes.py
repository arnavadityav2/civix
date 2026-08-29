import duckdb, glob, os
con = duckdb.connect(':memory:')
base = 'D:/civix_data/synthetic/profile_a'
tables = [
    'persons', 'organisations', 'phones', 'sims', 'devices', 'locations', 'cell_sectors', 'accounts',
    'cdrs', 'transactions', 'cases', 'case_entity_roles',
    'ground_truth/person_labels', 'ground_truth/train_val_test_split',
    'ml_features'
]
total_cols = 0
all_cols = set()
for t in tables:
    if t == 'ml_features':
        paths = glob.glob(f'{base}/{t}/*.parquet')
    elif t == 'cdrs':
        paths = glob.glob(f'{base}/{t}/**/*.parquet', recursive=True)
    else:
        paths = glob.glob(f'{base}/{t}/*.parquet')
    
    if not paths: continue
    
    for path in paths:
        path = path.replace('\\\\', '/')
        try:
            cols = [r[0] for r in con.execute(f"DESCRIBE SELECT * FROM read_parquet('{path}')").fetchall()]
            filename = os.path.basename(path)
            if t == 'ml_features':
                print(f'{filename.ljust(45)}: {len(cols):>2} attributes -> {cols}')
            else:
                print(f'{t.ljust(45)}: {len(cols):>2} attributes -> {cols}')
            
            total_cols += len(cols)
            all_cols.update(cols)
            
            if t != 'ml_features':
                break
        except Exception as e:
            print(f'Error on {t} ({path}): {e}')

print(f'\nTotal Attributes (including overlap across tables): {total_cols}')
print(f'Total UNIQUE Attributes: {len(all_cols)}')
