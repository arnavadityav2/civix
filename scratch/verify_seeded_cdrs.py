import psycopg2
import duckdb
from neo4j import GraphDatabase

def main():
    print("=== VERIFYING SEEDED CDR DATA FOR CASE CIV-2012-001 ===")
    
    # 1. PostgreSQL Check
    conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    cur.execute("""
        SELECT e.event_id, e.event_type, lower(e.occurred_at) as call_time, e.description,
               cp.msisdn as caller_msisdn, ca.msisdn as callee_msisdn
        FROM civix.event e
        JOIN civix.event_location el ON e.event_id = el.event_id
        JOIN civix.investigative_case c ON el.case_id = c.case_id
        LEFT JOIN civix.event_participant ep1 ON e.event_id = ep1.event_id AND ep1.participant_role = 'CALLER'
        LEFT JOIN civix.phone_number cp ON ep1.entity_id = cp.entity_id
        LEFT JOIN civix.event_participant ep2 ON e.event_id = ep2.event_id AND ep2.participant_role = 'CALLEE'
        LEFT JOIN civix.phone_number ca ON ep2.entity_id = ca.entity_id
        WHERE c.case_number = 'CIV-2012-001' AND e.event_type = 'CALL'
        ORDER BY lower(e.occurred_at) ASC
    """)
    pg_events = cur.fetchall()
    print(f"\n1. POSTGRESQL TELECOM CALL EVENTS FOR CIV-2012-001 ({len(pg_events)}):")
    for r in pg_events:
        print(f"  - [{r[2]}] {r[4]} ---> {r[5]} ({r[3]})")

    # 2. DuckDB / Parquet Check
    duck = duckdb.connect()
    parquet_path = "demo_world_15k_output/cdrs/year=2026/month=3/planted_van_robbery.parquet"
    parquet_cdrs = duck.execute(f"SELECT cdr_id, caller_phone_id, callee_phone_id, timestamp, duration_seconds, call_type FROM '{parquet_path}'").fetchdf()
    print(f"\n2. PARQUET PLANTED CDR RECORDS ({len(parquet_cdrs)}):")
    print(parquet_cdrs.head(10).to_string(index=False))

    # 3. Neo4j Check
    driver = GraphDatabase.driver('bolt://localhost:7688', auth=('neo4j', 'civix123456'))
    with driver.session() as session:
        res = session.run("""
            MATCH (p1)-[r:COMMUNICATED_WITH]->(p2)
            WHERE r.case_number = 'CIV-2012-001'
            RETURN p1.name as caller, r.call_count as calls, p2.name as callee
        """)
        print(f"\n3. NEO4J COMMUNICATED_WITH GRAPH EDGES FOR CIV-2012-001:")
        for row in res:
            print(f"  - {row['caller']} --(COMMUNICATED_WITH, {row['calls']} calls)--> {row['callee']}")
    driver.close()

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
