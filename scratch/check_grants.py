"""Check and grant permissions for civix_api user on Round 2 tables."""
import psycopg2

# Connect as postgres superuser
conn = psycopg2.connect(
    host='localhost', port=5433, dbname='civix_test',
    user='postgres', password='postgres'
)
cur = conn.cursor()
print("Connected as postgres superuser")

print("\n=== Checking current grants on evidence_artifact ===")
cur.execute("""
    SELECT grantee, privilege_type, is_grantable
    FROM information_schema.role_table_grants
    WHERE table_schema = 'civix' AND table_name = 'evidence_artifact'
    ORDER BY grantee, privilege_type
""")
for r in cur.fetchall():
    print(f"  {r}")

cur.close()
conn.close()
print("Done.")
