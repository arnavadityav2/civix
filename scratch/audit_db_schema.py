import psycopg
import json

dsn = "postgresql://postgres:postgres@localhost:5432/civix_demo"

conn = psycopg.connect(dsn)
cur = conn.cursor()

# 1. Get all tables in civix schema
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'civix' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = [r[0] for r in cur.fetchall()]

print(f"TOTAL BASE TABLES IN 'civix' SCHEMA: {len(tables)}\n")

schema_summary = {}

for t in tables:
    # Column details
    cur.execute("""
        SELECT column_name, data_type, udt_name, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'civix' AND table_name = %s
        ORDER BY ordinal_position;
    """, (t,))
    cols = cur.fetchall()
    
    # Row count
    cur.execute(f"SELECT count(*) FROM civix.{t}")
    cnt = cur.fetchone()[0]
    
    schema_summary[t] = {
        "count": cnt,
        "columns": [
            {
                "name": c[0],
                "type": c[1] if c[1] != 'USER-DEFINED' else c[2],
                "nullable": c[3] == 'YES',
                "default": c[4]
            } for c in cols
        ]
    }

with open("scratch/db_schema_audit.json", "w") as f:
    json.dump(schema_summary, f, indent=2, default=str)

print("Saved DB schema audit to scratch/db_schema_audit.json")
