import psycopg2
from neo4j import GraphDatabase

pg_dsn = "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test"

with psycopg2.connect(pg_dsn) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM civix.outbox")
        total = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL AND error_status IS NULL")
        pending = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NOT NULL")
        consumed = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM civix.outbox WHERE error_status = 'PERMANENT_FAILURE'")
        failed = cur.fetchone()[0]

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
with driver.session() as session:
    res = session.run("MATCH (n) RETURN count(n) as c")
    nodes = res.single()['c']
    res = session.run("MATCH ()-[r]->() RETURN count(r) as c")
    rels = res.single()['c']

print(f"PG outbox total: {total}")
print(f"PG outbox pending: {pending}")
print(f"PG outbox consumed: {consumed}")
print(f"PG outbox failed: {failed}")
print(f"Neo4j nodes: {nodes}")
print(f"Neo4j rels: {rels}")
