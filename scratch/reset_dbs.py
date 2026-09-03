import psycopg
from neo4j import GraphDatabase

PG_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

# Explicit allowlist of tables containing test/application data to wipe.
# System, auth, and schema migrations are untouched.
TABLES_TO_TRUNCATE = [
    "civix.entity", 
    "civix.investigative_case", 
    "civix.fir",
    "civix.event",
    "civix.hypothesis",
    "civix.assertion",
    "civix.investigative_lead",
    "civix.evidence_instance",
    "civix.investigation_task",
    "civix.outbox"
]

def run_reset():
    print("--- COMMENCING CONTROLLED RESET ---")
    
    # 1. PostgreSQL Reset
    with psycopg.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            tables_str = ", ".join(TABLES_TO_TRUNCATE)
            print(f"Executing TRUNCATE {tables_str} CASCADE;")
            cur.execute(f"TRUNCATE {tables_str} CASCADE;")
            conn.commit()
            print("PostgreSQL Reset Complete.")

    # 2. Neo4j Reset
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        print("Executing MATCH (n) DETACH DELETE n;")
        res = session.run("MATCH (n) DETACH DELETE n RETURN count(n) as cnt")
        print(f"Neo4j Nodes deleted: {res.single()['cnt']}")
    driver.close()
    
    print("--- RESET COMPLETE ---")

if __name__ == "__main__":
    run_reset()
