import psycopg
conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

# Get participant_role column type
cur.execute("""
    SELECT column_name, udt_name, is_nullable
    FROM information_schema.columns
    WHERE table_schema='civix' AND table_name='event_participant'
""")
print("event_participant columns:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} udt={r[1]}, nullable={r[2]}")

# Get all civix custom types
cur.execute("""
    SELECT typname, typtype FROM pg_type 
    WHERE typnamespace = (SELECT oid FROM pg_namespace WHERE nspname='civix')
    AND typtype = 'e'
    ORDER BY typname
""")
print("\nAll civix enum types:")
for r in cur.fetchall():
    print(f"  {r[0]}")
    cur2 = conn.cursor()
    cur2.execute(f"SELECT unnest(enum_range(NULL::civix.{r[0]}))::text ORDER BY 1")
    vals = [x[0] for x in cur2.fetchall()]
    print(f"    {vals}")

# Check source_identity
cur.execute("""
    SELECT column_name, udt_name, is_nullable
    FROM information_schema.columns
    WHERE table_schema='civix' AND table_name='source_identity'
    ORDER BY ordinal_position
""")
print("\nsource_identity columns (with udt):")
for r in cur.fetchall():
    print(f"  {r[0]:30s} udt={r[1]}, nullable={r[2]}")

conn.close()
