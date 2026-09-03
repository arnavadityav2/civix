import psycopg

conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

# Check tables critical for entity mapper
tables = ['source_identity', 'person', 'organization', 'location', 'vehicle', 'financial_account', 'event', 'event_participant', 'assertion']
for t in tables:
    cur.execute(f"""
        SELECT column_name, data_type, column_default, is_nullable 
        FROM information_schema.columns 
        WHERE table_schema='civix' AND table_name='{t}' 
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print(f"\n=== {t} ===")
    for c in cols:
        print(f"  {c[0]:30s} {c[1]:25s} nullable={c[3]} default={c[2]}")

# Check predicate enum values
cur.execute("SELECT unnest(enum_range(NULL::civix.predicate_enum))::text ORDER BY 1")
predicates = [r[0] for r in cur.fetchall()]
print(f"\n=== predicate_enum ({len(predicates)} values) ===")
for p in predicates:
    print(f"  {p}")

# Check event_type enum
cur.execute("SELECT unnest(enum_range(NULL::civix.event_type_enum))::text ORDER BY 1")
event_types = [r[0] for r in cur.fetchall()]
print(f"\n=== event_type_enum ===")
print(event_types)

# Check entity_type enum
cur.execute("SELECT unnest(enum_range(NULL::civix.entity_type_enum))::text ORDER BY 1")
entity_types = [r[0] for r in cur.fetchall()]
print(f"\n=== entity_type_enum ===")
print(entity_types)

# Check epistemic status enum
cur.execute("SELECT unnest(enum_range(NULL::civix.epistemic_status_enum))::text ORDER BY 1")
epistemic = [r[0] for r in cur.fetchall()]
print(f"\n=== epistemic_status_enum ===")
print(epistemic)

# Check if location has geometry requirement
cur.execute("""
    SELECT column_name, is_nullable FROM information_schema.columns 
    WHERE table_schema='civix' AND table_name='location'
    AND column_name IN ('geometry', 'location_type')
""")
print("\n=== location nullable check ===")
for r in cur.fetchall():
    print(f"  {r[0]}: nullable={r[1]}")

# Check event_participant unique constraint
cur.execute("""
    SELECT constraint_name, constraint_type 
    FROM information_schema.table_constraints 
    WHERE table_schema='civix' AND table_name='event_participant'
""")
print("\n=== event_participant constraints ===")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
