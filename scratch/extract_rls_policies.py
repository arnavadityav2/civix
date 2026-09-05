import psycopg
import json

dsn = "postgresql://postgres:postgres@localhost:5432/civix_demo"
conn = psycopg.connect(dsn)
cur = conn.cursor()

cur.execute("""
    SELECT 
        schemaname,
        tablename,
        policyname,
        permissive,
        roles,
        cmd,
        qual,
        with_check
    FROM pg_policies
    WHERE schemaname = 'civix';
""")

policies = [
    {
        "table": r[1],
        "policy_name": r[2],
        "permissive": r[3],
        "roles": r[4],
        "cmd": r[5],
        "qual": r[6],
        "with_check": r[7]
    } for r in cur.fetchall()
]

with open("scratch/rls_policies.json", "w") as f:
    json.dump(policies, f, indent=2)

print("Saved RLS policies to scratch/rls_policies.json")
