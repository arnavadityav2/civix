import psycopg
conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

# location_type_enum
cur.execute("SELECT unnest(enum_range(NULL::civix.location_type_enum))::text ORDER BY 1")
print("location_type_enum:", [r[0] for r in cur.fetchall()])

# event_participant_role_enum
cur.execute("SELECT unnest(enum_range(NULL::civix.event_participant_role_enum))::text ORDER BY 1")
print("event_participant_role_enum:", [r[0] for r in cur.fetchall()])

# uq_event_participant — what columns?
cur.execute("""
    SELECT indexname, indexdef FROM pg_indexes 
    WHERE schemaname='civix' AND tablename='event_participant'
""")
for r in cur.fetchall():
    print(f"Index: {r[0]} = {r[1]}")

# source_identity columns
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema='civix' AND table_name='source_identity'
    ORDER BY ordinal_position
""")
print("\nsource_identity columns:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]:25s} nullable={r[2]} default={r[3]}")

# identifier_type enum
try:
    cur.execute("SELECT unnest(enum_range(NULL::civix.identifier_type_enum))::text ORDER BY 1")
    print("identifier_type_enum:", [r[0] for r in cur.fetchall()])
except Exception as e:
    print(f"identifier_type not an enum: {e}")

conn.close()
