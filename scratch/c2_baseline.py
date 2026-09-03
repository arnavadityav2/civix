import psycopg2
from neo4j import GraphDatabase

PG_DSN = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASS = "password"

def get_baseline():
    print("--- BASELINE START ---")
    
    with psycopg2.connect(PG_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM civix.person")
            pg_persons = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM civix.source_identity")
            pg_sources = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM civix.identity_candidate")
            pg_candidates = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM civix.identity_resolution")
            pg_resolutions = cur.fetchone()[0]
            print(f"PG civix.person: {pg_persons}")
            print(f"PG civix.source_identity: {pg_sources}")
            print(f"PG civix.identity_candidate: {pg_candidates}")
            print(f"PG civix.identity_resolution: {pg_resolutions}")
            
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    with driver.session() as session:
        n_person = session.run("MATCH (n:Person) RETURN count(n)").single()[0]
        n_identity = session.run("MATCH (n:Identity) RETURN count(n)").single()[0]
        n_candidates = session.run("MATCH ()-[r:CANDIDATE_FOR]->() RETURN count(r)").single()[0]
        n_resolves = session.run("MATCH ()-[r:RESOLVES_TO]->() RETURN count(r)").single()[0]
        print(f"Neo4j Person nodes: {n_person}")
        print(f"Neo4j Identity nodes: {n_identity}")
        print(f"Neo4j CANDIDATE_FOR edges: {n_candidates}")
        print(f"Neo4j RESOLVES_TO edges: {n_resolves}")
    driver.close()
    print("--- BASELINE END ---")

if __name__ == "__main__":
    get_baseline()
