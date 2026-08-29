"""Profile A dataset explorer — python scripts/explore_profile_a.py"""
import duckdb, os, sys, json
sys.stdout.reconfigure(encoding="utf-8")

base = "D:/civix_data/synthetic/profile_a"
cdr_path = f"{base}/cdrs/year=2025/month=4/*.parquet"
con = duckdb.connect(":memory:")

def q(sql):
    return con.execute(sql).fetchall()

def header(title):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print(f"{'='*65}")

# -- Manifest -----------------------------------------------------------------
with open(os.path.join(base.replace("/","\\"), "manifest.json")) as f:
    mf = json.load(f)

header("MANIFEST SUMMARY")
print(f"  Profile  : {mf['profile']}")
print(f"  Seed     : {mf['seed']}")
print(f"  Duration : {mf['generation_duration_seconds']}s")
print(f"  Total rows  : {mf['total_rows']:,}")
print(f"  Total size  : {mf['total_bytes'] // (1024*1024)} MB")
print(f"\n  Entity row counts:")
for k, v in sorted(mf["row_counts"].items()):
    print(f"    {k:<35} {v:>10,}")

# -- Persons ------------------------------------------------------------------
header("PERSONS — 5 SAMPLE ROWS")
rows = q(f"""
    SELECT person_index, full_name, gender, date_of_birth,
           occupation, scenario_class, risk_score
    FROM read_parquet('{base}/persons/*.parquet')
    ORDER BY person_index LIMIT 5
""")
print(f"  {'#':<5} {'Name':<22} {'Gender':<7} {'DOB':<12} {'Occupation':<25} {'Class':<20} {'Risk'}")
print(f"  {'-'*105}")
for r in rows:
    print(f"  {r[0]:<5} {r[1]:<22} {r[2]:<7} {r[3]:<12} {r[4]:<25} {r[5]:<20} {r[6]:.2f}")

# -- Scenario distribution ----------------------------------------------------
header("SCENARIO CLASS DISTRIBUTION")
rows = q(f"""
    SELECT scenario_class, COUNT(*) as n, ROUND(COUNT(*)*100.0/1000,1) as pct
    FROM read_parquet('{base}/persons/*.parquet')
    GROUP BY scenario_class ORDER BY n DESC
""")
for r in rows:
    bar = "#" * int(r[2] / 2)
    print(f"  {r[0]:<22} {r[1]:>5} persons  ({r[2]:>5}%)  {bar}")

# -- Ground truth labels ------------------------------------------------------
header("GROUND TRUTH LABEL FAMILIES (top 12)")
rows = q(f"""
    SELECT scenario_family, scenario_category, scenario_class,
           COUNT(*) as n, ROUND(AVG(risk_score_gt),2) as avg_risk
    FROM read_parquet('{base}/ground_truth/person_labels/*.parquet')
    WHERE is_positive_label = true OR is_false_positive = true
    GROUP BY scenario_family, scenario_category, scenario_class
    ORDER BY n DESC LIMIT 12
""")
print(f"  {'Family':<35} {'Category':<20} {'Class':<20} {'N':>4} {'AvgRisk':>7}")
print(f"  {'-'*90}")
for r in rows:
    print(f"  {r[0]:<35} {r[1]:<20} {r[2]:<20} {r[3]:>4} {r[4]:>7.2f}")

# -- Hardest persons (high risk confirmed positive) ---------------------------
header("TOP 8 HIGHEST-RISK CONFIRMED PERSONS")
rows = q(f"""
    SELECT p.full_name, p.gender, p.occupation,
           l.scenario_class, l.scenario_family, l.difficulty,
           ROUND(l.risk_score_gt,3) as risk, l.is_false_positive
    FROM read_parquet('{base}/ground_truth/person_labels/*.parquet') l
    JOIN read_parquet('{base}/persons/*.parquet') p
      ON l.entity_id = p.person_id
    WHERE l.is_positive_label = true
    ORDER BY l.risk_score_gt DESC LIMIT 8
""")
print(f"  {'Name':<22} {'Occ':<18} {'Risk':>5}  {'Class':<20} {'Family':<30} {'Diff':<8} {'FP?'}")
print(f"  {'-'*115}")
for r in rows:
    fp = "YES" if r[7] else "-"
    print(f"  {r[0]:<22} {r[2]:<18} {r[6]:>5}  {r[3]:<20} {r[4]:<30} {r[5]:<8} {fp}")

# -- CDRs ---------------------------------------------------------------------
header("CDRs — 8 SAMPLE ROWS")
rows = q(f"""
    SELECT cdr_id, caller_person_id, callee_phone_id, timestamp,
           duration_seconds, call_type, cell_sector_id
    FROM read_parquet('{cdr_path}')
    LIMIT 8
""")
print(f"  {'Caller (person_id truncated)':<20} {'Callee phone':<22} {'Timestamp':<22} {'Dur':>4} {'Type':<6} {'Cell'}")
print(f"  {'-'*100}")
for r in rows:
    print(f"  {r[1][-20:]:<20} {r[2]:<22} {r[3]:<22} {r[4]:>4}s {r[5]:<6} {r[6]}")

header("CDR STATISTICS")
rows = q(f"""
    SELECT COUNT(*) as total,
           COUNT(DISTINCT caller_person_id) as callers,
           COUNT(DISTINCT callee_phone_id) as callees,
           COUNT(DISTINCT cell_sector_id) as sectors,
           ROUND(AVG(duration_seconds)) as avg_dur,
           MIN(timestamp) as earliest, MAX(timestamp) as latest
    FROM read_parquet('{cdr_path}')
""")
r = rows[0]
print(f"  Total CDRs          : {r[0]:,}")
print(f"  Unique callers      : {r[1]:,}")
print(f"  Unique callees      : {r[2]:,}")
print(f"  Unique cell sectors : {r[3]:,}")
print(f"  Avg call duration   : {r[4]}s (~{int(r[4])//60}m {int(r[4])%60}s)")
print(f"  Date range          : {r[5]} to {r[6]}")

rows = q(f"""
    SELECT call_type, COUNT(*) as n, ROUND(COUNT(*)*100.0/250000,1) as pct
    FROM read_parquet('{cdr_path}')
    GROUP BY call_type ORDER BY n DESC
""")
print(f"\n  Call type mix:")
for r in rows:
    bar = "#" * int(r[2] / 2)
    print(f"    {r[0]:<8} {r[1]:>8,}  ({r[2]}%)  {bar}")

# -- Busiest persons ----------------------------------------------------------
header("TOP 10 BUSIEST PERSONS (CDR activity)")
rows = q(f"""
    SELECT p.full_name, p.scenario_class, p.occupation,
           COUNT(*) as cdrs,
           COUNT(DISTINCT c.callee_phone_id) as contacts,
           COUNT(DISTINCT c.cell_sector_id) as sectors
    FROM read_parquet('{cdr_path}') c
    JOIN read_parquet('{base}/persons/*.parquet') p
      ON c.caller_person_id = p.person_id
    GROUP BY p.full_name, p.scenario_class, p.occupation
    ORDER BY cdrs DESC LIMIT 10
""")
print(f"  {'Name':<22} {'CDRs':>6}  {'Contacts':>8}  {'Sectors':>7}  {'Class':<20} {'Occupation'}")
print(f"  {'-'*95}")
for r in rows:
    print(f"  {r[0]:<22} {r[3]:>6}  {r[4]:>8}  {r[5]:>7}  {r[1]:<20} {r[2]}")

# -- Transactions -------------------------------------------------------------
header("TRANSACTION STATISTICS")
rows = q(f"""
    SELECT COUNT(*) as n,
           ROUND(SUM(amount)) as total,
           ROUND(AVG(amount)) as avg_amt,
           ROUND(MAX(amount)) as max_amt,
           ROUND(MIN(amount)) as min_amt,
           COUNT(DISTINCT transaction_type) as types
    FROM read_parquet('{base}/transactions/*.parquet')
""")
r = rows[0]
print(f"  Total transactions : {r[0]:,}")
print(f"  Total amount       : INR {r[1]:>15,.0f}")
print(f"  Average per txn    : INR {r[2]:>15,.0f}")
print(f"  Largest txn        : INR {r[3]:>15,.0f}")
print(f"  Smallest txn       : INR {r[4]:>15,.0f}")
print(f"  Transaction types  : {r[5]}")

rows = q(f"""
    SELECT transaction_type, COUNT(*) as n, ROUND(AVG(amount)) as avg_amt
    FROM read_parquet('{base}/transactions/*.parquet')
    GROUP BY transaction_type ORDER BY n DESC
""")
print(f"\n  By type:")
for r in rows:
    print(f"    {r[0]:<20} {r[1]:>7,} txns  avg INR {r[2]:>10,.0f}")

# -- ML Features --------------------------------------------------------------
header("ML FEATURES — COMMUNICATION (top 10 by call volume)")
rows = q(f"""
    SELECT f.person_id, p.full_name, p.scenario_class,
           f.total_calls, f.unique_callees, f.unique_cell_sectors,
           ROUND(f.avg_call_duration_sec) as avg_dur,
           f.voice_calls, f.sms_count, f.data_sessions
    FROM read_parquet('{base}/ml_features/person_communication_features.parquet') f
    JOIN read_parquet('{base}/persons/*.parquet') p ON f.person_id = p.person_id
    ORDER BY f.total_calls DESC LIMIT 10
""")
print(f"  {'Name':<22} {'Calls':>6}  {'Contacts':>8}  {'Sectors':>7}  {'AvgDur':>6}  {'Voice':>7}  {'SMS':>7}  {'Data':>6}  {'Class'}")
print(f"  {'-'*110}")
for r in rows:
    print(f"  {r[1]:<22} {r[3]:>6}  {r[4]:>8}  {r[5]:>7}  {r[6]:>6}s  {r[7]:>7}  {r[8]:>7}  {r[9]:>6}  {r[2]}")

# -- Train/Val/Test split -----------------------------------------------------
header("TRAIN / VALIDATION / TEST SPLIT")
rows = q(f"""
    SELECT split, COUNT(*) as n
    FROM read_parquet('{base}/ground_truth/train_val_test_split/*.parquet')
    GROUP BY split ORDER BY split
""")
total = sum(r[1] for r in rows)
for r in rows:
    pct = r[1]*100//total
    bar = "#" * (pct // 2)
    print(f"  {r[0]:<12} {r[1]:>5} persons  ({pct}%)  {bar}")

print("\n")
