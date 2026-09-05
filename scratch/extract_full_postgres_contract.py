import psycopg
import json

dsn = "postgresql://postgres:postgres@localhost:5432/civix_demo"
conn = psycopg.connect(dsn)
cur = conn.cursor()

# 1. Get all 63 tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'civix' AND table_type = 'BASE TABLE'
    ORDER BY table_name;
""")
tables = [r[0] for r in cur.fetchall()]

full_contract = {}

for t in tables:
    # Columns
    cur.execute("""
        SELECT 
            c.column_name, 
            c.data_type, 
            c.udt_name, 
            c.is_nullable, 
            c.column_default,
            c.is_generated
        FROM information_schema.columns c
        WHERE c.table_schema = 'civix' AND c.table_name = %s
        ORDER BY c.ordinal_position;
    """, (t,))
    columns = [
        {
            "name": r[0],
            "type": r[2] if r[1] == 'USER-DEFINED' else r[1],
            "nullable": r[3] == 'YES',
            "default": r[4],
            "generated": r[5] != 'NEVER'
        } for r in cur.fetchall()
    ]
    
    # Primary Key
    cur.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY' 
          AND tc.table_schema = 'civix' AND tc.table_name = %s;
    """, (t,))
    pk = [r[0] for r in cur.fetchall()]
    
    # Foreign Keys
    cur.execute("""
        SELECT
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name,
            rc.update_rule,
            rc.delete_rule
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name AND ccu.table_schema = tc.table_schema
        JOIN information_schema.referential_constraints rc
          ON rc.constraint_name = tc.constraint_name AND rc.constraint_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'civix' AND tc.table_name = %s;
    """, (t,))
    fks = [
        {
            "column": r[0],
            "foreign_table": r[1],
            "foreign_column": r[2],
            "on_update": r[3],
            "on_delete": r[4]
        } for r in cur.fetchall()
    ]

    # Unique Constraints
    cur.execute("""
        SELECT tc.constraint_name, kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'UNIQUE' 
          AND tc.table_schema = 'civix' AND tc.table_name = %s;
    """, (t,))
    uniques = [r[1] for r in cur.fetchall()]

    # Triggers
    cur.execute("""
        SELECT trigger_name, action_statement, action_timing, event_manipulation
        FROM information_schema.triggers
        WHERE event_object_schema = 'civix' AND event_object_table = %s;
    """, (t,))
    triggers = [
        {
            "name": r[0],
            "timing": r[2],
            "event": r[3],
            "statement": r[1]
        } for r in cur.fetchall()
    ]
    
    full_contract[t] = {
        "columns": columns,
        "primary_key": pk,
        "foreign_keys": fks,
        "unique_constraints": uniques,
        "triggers": triggers
    }

with open("scratch/full_postgres_contract.json", "w") as f:
    json.dump(full_contract, f, indent=2)

print("Extracted full PostgreSQL contract for all 63 tables to scratch/full_postgres_contract.json")
