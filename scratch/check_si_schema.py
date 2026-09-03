"""Deep check source_identity schema and constraints."""
import psycopg2
ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"
conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'
)
cur = conn.cursor()
cur.execute("SELECT set_config('app.current_user_id', %s, false), set_config('civix.current_user_id', %s, false)", (ADMIN_USER_ID, ADMIN_USER_ID))

print("=== source_identity: detailed columns with defaults/nullability ===")
cur.execute("""
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns
    WHERE table_schema = 'civix' AND table_name = 'source_identity'
    ORDER BY ordinal_position
""")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== source_identity constraints ===")
cur.execute("""
    SELECT conname, contype, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'civix.source_identity'::regclass
    ORDER BY conname
""")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== event_participant constraints ===")
cur.execute("""
    SELECT conname, contype, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'civix.event_participant'::regclass
    ORDER BY conname
""")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== entity constraints ===")
cur.execute("""
    SELECT conname, contype, pg_get_constraintdef(oid)
    FROM pg_constraint
    WHERE conrelid = 'civix.entity'::regclass
    ORDER BY conname
""")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== entity_type_enum values ===")
cur.execute("""
    SELECT enumlabel FROM pg_enum
    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'entity_type_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix'))
    ORDER BY enumsortorder
""")
for r in cur.fetchall():
    print(f"  {r[0]}")

print("\n=== source_identity_type_enum values ===")
cur.execute("""
    SELECT enumlabel FROM pg_enum
    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'source_identity_type_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix'))
    ORDER BY enumsortorder
""")
for r in cur.fetchall():
    print(f"  {r[0]}")

cur.close()
conn.close()
print("\nDone.")
