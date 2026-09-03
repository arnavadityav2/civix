import psycopg
conn = psycopg.connect("postgresql://postgres:postgres@localhost:5433/civix_test")
cur = conn.cursor()

cur.execute("""SELECT column_name, udt_name, is_nullable FROM information_schema.columns
WHERE table_schema='civix' AND table_name='case_access'
ORDER BY ordinal_position""")
print("case_access columns:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]:20s} nullable={r[2]}")

# Also check permission_level values
cur.execute("SELECT unnest(enum_range(NULL::civix.case_permission_enum))::text")
print("\ncase_permission_enum:", [r[0] for r in cur.fetchall()])

# Check existing cases + access
cur.execute("SELECT case_id, title, case_type, jurisdiction FROM civix.investigative_case LIMIT 3")
cases = cur.fetchall()
print("\nExisting cases:")
for r in cases:
    print(f"  {r[0]} {r[1]!r} {r[2]} {r[3]}")

if cases:
    cid = cases[0][0]
    cur.execute("SELECT user_id, permission_level, is_revoked FROM civix.case_access WHERE case_id = %s LIMIT 5", (cid,))
    print(f"\nAccess for case {cid}:")
    for r in cur.fetchall():
        print(f"  user={r[0]} perm={r[1]} revoked={r[2]}")

conn.close()
