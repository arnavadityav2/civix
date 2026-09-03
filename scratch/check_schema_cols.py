"""Check analysis_run columns."""
import psycopg2
ADMIN_USER_ID = "3c3ba8b7-7f44-401d-a0ac-4c4747650883"
conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='civix_api', password='cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx'
)
cur = conn.cursor()
cur.execute("SELECT set_config('app.current_user_id', %s, false), set_config('civix.current_user_id', %s, false)", (ADMIN_USER_ID, ADMIN_USER_ID))

print("=== analysis_run columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'analysis_run' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== observation columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'observation' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== extraction columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'extraction' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== provenance columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'provenance' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== source_record columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'source_record' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== entity columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'entity' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== source_identity columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'source_identity' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== event columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'event' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== event_participant columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'event_participant' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== assertion columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'assertion' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

print("\n=== evidence_instance columns ===")
cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_schema = 'civix' AND table_name = 'evidence_instance' ORDER BY ordinal_position")
for r in cur.fetchall():
    print(f"  {r}")

cur.close()
conn.close()
print("\nDone.")
