import psycopg
from neo4j import GraphDatabase

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

def run_snapshot():
    output = []
    output.append("--- PRE-RESET SNAPSHOT & INVENTORY ---")

    # POSTGRESQL
    output.append("\n--- POSTGRESQL INVENTORY ---")
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            # 1. Tables and row counts
            output.append("\n[TABLES & ROW COUNTS]")
            cur.execute("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema IN ('civix', 'auth') 
                ORDER BY table_schema, table_name
            """)
            tables = cur.fetchall()
            for schema, name in tables:
                cur.execute(f"SELECT COUNT(*) FROM {schema}.{name}")
                count = cur.fetchone()[0]
                output.append(f"{schema}.{name}: {count} rows")

            # 2. Foreign Keys
            output.append("\n[FOREIGN KEYS]")
            cur.execute("""
                SELECT
                    tc.table_schema, 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_schema AS foreign_table_schema,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema IN ('civix', 'auth');
            """)
            fkeys = cur.fetchall()
            for fk in fkeys:
                output.append(f"{fk[0]}.{fk[1]}.{fk[2]} -> {fk[3]}.{fk[4]}.{fk[5]}")

            # 3. Triggers
            output.append("\n[TRIGGERS]")
            cur.execute("""
                SELECT event_object_schema, event_object_table, trigger_name, action_statement
                FROM information_schema.triggers
                WHERE event_object_schema IN ('civix', 'auth')
            """)
            triggers = cur.fetchall()
            for trg in triggers:
                output.append(f"{trg[0]}.{trg[1]} -> {trg[2]} ({trg[3]})")

            # 4. RLS Policies
            output.append("\n[RLS POLICIES]")
            cur.execute("""
                SELECT schemaname, tablename, policyname, roles, cmd, qual, with_check 
                FROM pg_policies 
                WHERE schemaname IN ('civix', 'auth')
            """)
            policies = cur.fetchall()
            for pol in policies:
                output.append(f"{pol[0]}.{pol[1]}: {pol[2]} (Roles: {pol[3]}, Cmd: {pol[4]})")

            # 5. Outbox metrics
            output.append("\n[OUTBOX METRICS]")
            cur.execute("SELECT COUNT(*) FROM civix.outbox WHERE consumed_at IS NOT NULL")
            output.append(f"Consumed outbox events: {cur.fetchone()[0]}")
            cur.execute("SELECT COUNT(*) FROM civix.outbox WHERE consumed_at IS NULL")
            output.append(f"Unconsumed outbox events: {cur.fetchone()[0]}")
            cur.execute("SELECT COUNT(*) FROM civix.outbox WHERE error_status IS NOT NULL")
            output.append(f"Failed outbox events: {cur.fetchone()[0]}")

    # NEO4J
    output.append("\n--- NEO4J INVENTORY ---")
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session() as session:
            # Version
            res = session.run("CALL dbms.components() YIELD name, versions, edition UNWIND versions AS version RETURN name, version, edition")
            for r in res:
                output.append(f"Version: {r['name']} {r['version']} {r['edition']}")
                
            # Nodes
            res = session.run("MATCH (n) RETURN COUNT(n) as cnt")
            output.append(f"Total Nodes: {res.single()['cnt']}")
            
            # Relationships
            res = session.run("MATCH ()-[r]->() RETURN COUNT(r) as cnt")
            output.append(f"Total Relationships: {res.single()['cnt']}")
            
            # Constraints/Indexes
            res = session.run("SHOW CONSTRAINTS")
            output.append("\n[CONSTRAINTS]")
            for r in res:
                output.append(f"{r['name']}: {r['labelsOrTypes']} {r['properties']} {r['type']}")
                
            res = session.run("SHOW INDEXES")
            output.append("\n[INDEXES]")
            for r in res:
                output.append(f"{r['name']}: {r['labelsOrTypes']} {r['properties']} {r['type']}")
                
        driver.close()
    except Exception as e:
        output.append(f"Neo4j Error: {e}")

    final_report = "\n".join(output)
    print(final_report)
    with open("c:\\Users\\ARNAV ADITYA\\Desktop\\civix 2.0\\scratch\\pre_reset_snapshot.txt", "w") as f:
        f.write(final_report)

if __name__ == "__main__":
    run_snapshot()
