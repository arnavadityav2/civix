import psycopg
from neo4j import GraphDatabase

PG_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

# Mapping pg type to Neo4j Label and ID key
ENTITY_MAP = {
    'person': ('Person', 'entity_id'),
    'investigative_case': ('Case', 'case_id'),
    'device': ('Device', 'entity_id'),
    'event': ('Event', 'event_id'),
    'assertion': ('Assertion', 'assertion_id'),
    'source_identity': ('Identity', 'entity_id')
}

def run_reconciliation():
    print("--- CIVIX 2.0 RECONCILIATION REPORT ---")
    pg_nodes = {}
    
    # 1. Fetch from PG
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            for pg_table, (n4j_label, id_field) in ENTITY_MAP.items():
                try:
                    cur.execute(f"SELECT {id_field} FROM civix.{pg_table}")
                    pg_nodes[n4j_label] = set(str(row[0]) for row in cur.fetchall())
                except Exception as e:
                    print(f"Skipping {pg_table}: {e}")
                    conn.rollback()

            # Edges
            cur.execute("SELECT role_id, case_id, entity_id FROM civix.case_entity_role WHERE tx_end IS NULL")
            pg_edges = set((str(r[1]), str(r[2])) for r in cur.fetchall())

    # 2. Fetch from Neo4j
    n4j_nodes = {}
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        for pg_table, (n4j_label, id_field) in ENTITY_MAP.items():
            res = session.run(f"MATCH (n:{n4j_label}) RETURN n.{id_field}")
            n4j_nodes[n4j_label] = set(str(r[0]) for r in res)
            
        res = session.run("MATCH (c:Case)-[r:HAS_ROLE]->(e) RETURN c.case_id, e.entity_id")
        n4j_edges = set((str(r[0]), str(r[1])) for r in res)
        
    driver.close()

    # 3. Compare
    passed = True
    for label in pg_nodes.keys():
        pg_set = pg_nodes[label]
        n4j_set = n4j_nodes.get(label, set())
        
        missing_in_neo = pg_set - n4j_set
        extra_in_neo = n4j_set - pg_set
        
        if missing_in_neo or extra_in_neo:
            passed = False
            print(f"\n[MISMATCH] Label: {label}")
            if missing_in_neo:
                print(f"  Missing in Neo4j: {missing_in_neo}")
            if extra_in_neo:
                print(f"  Extra in Neo4j (Unexpected): {extra_in_neo}")
        else:
            print(f"[OK] Label: {label} (Count: {len(pg_set)})")

    # Edge compare
    missing_edges = pg_edges - n4j_edges
    extra_edges = n4j_edges - pg_edges
    if missing_edges or extra_edges:
        passed = False
        print(f"\n[MISMATCH] Relationships (case_entity_role -> HAS_ROLE)")
        if missing_edges:
            print(f"  Missing in Neo4j: {missing_edges}")
        if extra_edges:
            print(f"  Extra in Neo4j: {extra_edges}")
    else:
        print(f"[OK] Relationships (case_entity_role -> HAS_ROLE) (Count: {len(pg_edges)})")

    print(f"\nRECONCILIATION RESULT: {'PASS' if passed else 'FAIL'}")

if __name__ == "__main__":
    run_reconciliation()
