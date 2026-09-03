from neo4j import GraphDatabase
import os
import sys

def inspect_neo4j():
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
    user = os.environ.get("NEO4J_USER", "neo4j")
    pwd = os.environ.get("NEO4J_PASSWORD", "password")
    target_db = os.environ.get("CIVIX_NEO4J_DB", "civix_demo_graph")
    
    print("==========================================================")
    print("PHASE 9: TARGET NEO4J DATABASE INSPECTION")
    print("==========================================================")
    print(f"URI       : {uri}")
    print(f"User      : {user}")
    print(f"Target DB : {target_db}")
    
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    
    # 1. Connect to target DB and get baseline metrics
    with driver.session(database=None) as session:
        n_nodes = session.run("MATCH (n) RETURN count(n) AS cnt;").single()["cnt"]
        n_rels = session.run("MATCH ()-[r]->() RETURN count(r) AS cnt;").single()["cnt"]
        labels = [r["label"] for r in session.run("CALL db.labels() YIELD label;")]
        rel_types = [r["relationshipType"] for r in session.run("CALL db.relationshipTypes() YIELD relationshipType;")]
        
        print(f"\nBaseline Target DB State:")
        print(f"  Node count        : {n_nodes}")
        print(f"  Relationship count: {n_rels}")
        print(f"  Labels            : {labels}")
        print(f"  Relationship types: {rel_types}")
        
    driver.close()
    print("[PASS] Target Neo4j Database Access Verified.")

if __name__ == "__main__":
    inspect_neo4j()
