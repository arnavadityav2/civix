import psycopg

conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

# 1. All civix tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='civix' ORDER BY table_name")
tables = [r[0] for r in cur.fetchall()]
print("=== CIVIX TABLES ===")
for t in tables:
    print(f"  {t}")

# 2. Evidence/provenance tables specifically
print("\n=== EVIDENCE/PROVENANCE TABLES COLUMNS ===")
for tbl in ['evidence_artifact', 'evidence_instance', 'source', 'source_record', 'provenance', 'observation', 'extraction', 'analysis_run']:
    cur.execute(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_schema='civix' AND table_name='{tbl}' ORDER BY ordinal_position")
    cols = cur.fetchall()
    print(f"\n{tbl}:")
    for col in cols:
        print(f"  {col[0]} ({col[1]}, nullable={col[2]})")

# 3. Triggers on key tables
print("\n=== KEY OUTBOX TRIGGERS ===")
cur.execute("""
    SELECT tgname, tgrelid::regclass 
    FROM pg_trigger 
    WHERE tgrelid::regclass::text LIKE 'civix.%' 
      AND NOT tgisinternal 
      AND tgname LIKE '%outbox%'
    ORDER BY tgrelid::regclass::text, tgname
""")
for r in cur.fetchall():
    print(f"  {r[1]}: {r[0]}")

# 4. Evidence_artifact has triggers?
cur.execute("""
    SELECT tgname FROM pg_trigger 
    WHERE tgrelid = 'civix.evidence_artifact'::regclass 
      AND NOT tgisinternal
""")
ev_triggers = [r[0] for r in cur.fetchall()]
print(f"\nevidence_artifact triggers: {ev_triggers}")

cur.execute("""
    SELECT tgname FROM pg_trigger 
    WHERE tgrelid = 'civix.evidence_instance'::regclass 
      AND NOT tgisinternal
""")
ei_triggers = [r[0] for r in cur.fetchall()]
print(f"evidence_instance triggers: {ei_triggers}")

conn.close()
