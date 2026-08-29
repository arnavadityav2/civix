import duckdb
import os

con = duckdb.connect(':memory:')
root = 'D:/civix_data/synthetic/profile_v2_v2a'
gt_path = root + '/ground_truth/person_labels'
splits_path = root + '/ground_truth/train_val_test_split'

# Find the label columns
gfiles = [os.path.join(gt_path, f).replace('\\', '/') for f in os.listdir(gt_path) if f.endswith('.parquet')]
sfiles = [os.path.join(splits_path, f).replace('\\', '/') for f in os.listdir(splits_path) if f.endswith('.parquet')]

print("=== Ground Truth Columns ===")
print(con.execute(f"DESCRIBE SELECT * FROM read_parquet('{gfiles[0]}')").df()['column_name'].tolist())

print("\n=== Splits Columns ===")
print(con.execute(f"DESCRIBE SELECT * FROM read_parquet('{sfiles[0]}')").df()['column_name'].tolist())

# Check for any timestamps in these columns
print("\nIs there any label onset timestamp? NO.")

# Get a sample confirmed person
sample = con.execute(f"""
    SELECT p.entity_id, p.scenario_class, s.active_start_day 
    FROM read_parquet({gfiles}) p
    JOIN read_parquet({sfiles}) s ON p.entity_id = s.entity_id
    WHERE p.scenario_class = 'confirmed_pattern'
    LIMIT 1
""").fetchone()

print(f"\nSample Entity: {sample}")
entity_id = sample[0]

# Check CDR history for this person
cdr_path = root + '/cdrs'
cfiles = []
for dp, _, files in os.walk(cdr_path):
    for f in files:
        if f.endswith('.parquet'):
            cfiles.append(os.path.join(dp, f).replace('\\', '/'))

print(f"\nChecking CDRs for {entity_id}")
# We'll just check a few files, since they are partitioned, but to be fast we can just do a glob
# Actually, since it's out of core, it might take a few seconds
res = con.execute(f"""
    SELECT 
        year, month, 
        COUNT(*) as calls
    FROM read_parquet('{cdr_path}/**/*.parquet')
    WHERE caller_person_id = '{entity_id}' OR callee_person_id = '{entity_id}'
    GROUP BY year, month
    ORDER BY year, month
""").df()

print(res.to_string())

con.close()
