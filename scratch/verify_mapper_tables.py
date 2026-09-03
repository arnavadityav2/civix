import psycopg
conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

tables = ['analysis_run', 'observation', 'extraction', 'provenance', 'source_record', 'source']
for t in tables:
    cur.execute(f"""
        SELECT column_name, udt_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema='civix' AND table_name='{t}'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print(f"\n=== {t} ===")
    for c in cols:
        print(f"  {c[0]:35s} {c[1]:25s} nullable={c[2]} default={str(c[3])[:40]}")

# Check extraction_type_enum values (we know it exists)
cur.execute("SELECT unnest(enum_range(NULL::civix.extraction_type_enum))::text ORDER BY 1")
print("\nextraction_type_enum:", [r[0] for r in cur.fetchall()])

# Check source agency_type — is it an enum or text?
cur.execute("""
    SELECT column_name, udt_name FROM information_schema.columns
    WHERE table_schema='civix' AND table_name='source'
    ORDER BY ordinal_position
""")
print("\nsource columns:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]}")

# Check observer_type in observation
cur.execute("""
    SELECT column_name, udt_name, is_nullable FROM information_schema.columns
    WHERE table_schema='civix' AND table_name='observation'
    ORDER BY ordinal_position
""")
print("\nobservation all columns:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]:25s} nullable={r[2]}")

# Check vehicle - registration_number unique constraint
cur.execute("""
    SELECT indexname, indexdef FROM pg_indexes 
    WHERE schemaname='civix' AND tablename='vehicle'
""")
print("\nvehicle indexes:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

conn.close()
