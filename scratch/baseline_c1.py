import psycopg2
from neo4j import GraphDatabase
import json

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"
neo4j_uri = "bolt://localhost:7687"
neo4j_auth = ("neo4j", "password")

def gather():
    out = {"pg": {}, "neo4j": {}}
    
    # PG state
    with psycopg2.connect(pg_dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM civix.outbox")
            out["pg"]["outbox_total"] = cur.fetchone()[0]
            
            cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL")
            out["pg"]["outbox_pending"] = cur.fetchone()[0]
            
            cur.execute("SELECT count(*) FROM civix.outbox WHERE error_status IS NOT NULL")
            out["pg"]["outbox_failed"] = cur.fetchone()[0]
            
            # oldest and newest pending
            cur.execute("SELECT id, created_at FROM civix.outbox WHERE consumed_at IS NULL ORDER BY created_at ASC LIMIT 1")
            row = cur.fetchone()
            out["pg"]["oldest_pending"] = str(row) if row else None
            
            cur.execute("SELECT id, created_at FROM civix.outbox WHERE consumed_at IS NULL ORDER BY created_at DESC LIMIT 1")
            row = cur.fetchone()
            out["pg"]["newest_pending"] = str(row) if row else None
            
            # sample pending events
            cur.execute("SELECT id, action, error_status, error_message FROM civix.outbox WHERE consumed_at IS NULL LIMIT 5")
            out["pg"]["sample_pending"] = cur.fetchall()
            
            # check available columns
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='civix' AND table_name='outbox'")
            out["pg"]["columns"] = [r[0] for r in cur.fetchall()]

    # Neo4j state
    with GraphDatabase.driver(neo4j_uri, auth=neo4j_auth) as driver:
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as node_count")
            out["neo4j"]["node_count"] = result.single()["node_count"]
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
            out["neo4j"]["rel_count"] = result.single()["rel_count"]

    with open("scratch/baseline_data.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
        
    print("Baseline gathered to scratch/baseline_data.json")

if __name__ == '__main__':
    gather()
