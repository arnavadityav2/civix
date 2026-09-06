import duckdb
import psycopg2
from neo4j import GraphDatabase

def main():
    print("=== DEEP DIAGNOSTIC: CASH VAN ROBBERY CDR DATA ===")
    
    # 1. DuckDB Query on partitioned Parquet CDR stores
    duck = duckdb.connect()
    
    p1 = "demo_world_15k_output/cdrs/**/*.parquet"
    cnt1 = duck.execute(f"SELECT COUNT(*) FROM '{p1}'").fetchone()[0]
    print(f"\n1. `demo_world_15k_output/cdrs` Total CDR Records: {cnt1:,}")
    
    p2 = "demo_output/cdrs/**/*.parquet"
    cnt2 = duck.execute(f"SELECT COUNT(*) FROM '{p2}'").fetchone()[0]
    print(f"2. `demo_output/cdrs` Total CDR Records: {cnt2:,}")

    # Inspect schema & sample of CDRs
    cols = duck.execute(f"SELECT * FROM '{p1}' LIMIT 1").fetchdf().columns.tolist()
    print(f"\n3. CDR PARQUET SCHEMA FIELDS: {cols}")

    # 2. Check Case Suspects in Postgres
    conn = psycopg2.connect(dbname='civix_demo', user='postgres', password='postgres', host='localhost', port=5432)
    cur = conn.cursor()

    cur.execute("""
        SELECT p.entity_id, p.display_name, cer.role
        FROM civix.case_entity_role cer
        JOIN civix.person p ON cer.entity_id = p.entity_id
        JOIN civix.investigative_case c ON cer.case_id = c.case_id
        WHERE c.case_number = 'CIV-2012-001'
    """)
    case_persons = cur.fetchall()
    print(f"\n4. PERSONS IN CASE CIV-2012-001 (Dwarka Sector 23 Cash Van Robbery):")
    p_names = []
    p_uuids = []
    for p in case_persons:
        print(f"   - [{p[2]}] {p[1]} (UUID: {p[0]})")
        p_names.append(p[1])
        p_uuids.append(str(p[0]))

    # Check Parquet CDRs for caller_person_id matching case persons
    if p_uuids:
        formatted_uuids = "', '".join(p_uuids)
        cdr_matches = duck.execute(f"""
            SELECT count(*) 
            FROM '{p1}' 
            WHERE caller_person_id IN ('{formatted_uuids}')
        """).fetchone()[0]
        print(f"\n5. PARQUET CDR DIRECT MATCHES FOR CIV-2012-001 PERSON UUIDs: {cdr_matches:,}")

    # Skip assertion check
    print(f"\n6. CHECKING NEO4J GRAPH LINKS FOR CASE ENTITIES...")

    # 3. Check Neo4j for COMMUNICATED_WITH edges between suspects
    driver = GraphDatabase.driver("bolt://localhost:7688", auth=("neo4j", "civix123456"))
    with driver.session() as session:
        print(f"\n7. NEO4J GRAPH CDR CONNECTIONS:")
        q = """
        MATCH (p1:Person)-[r:COMMUNICATED_WITH]-(p2:Person)
        WHERE p1.name IN $names OR p2.name IN $names
        RETURN p1.name as p1, type(r) as rel, p2.name as p2, r.call_count as count
        """
        res = list(session.run(q, names=p_names))
        print(f"   - Direct COMMUNICATED_WITH graph edges for case entities: {len(res)}")
        for r in res:
            print(f"     * {r['p1']} <--> {r['p2']} (Call Count: {r['count']})")

        # Check all relationships connected to Suresh Valmiki in Neo4j
        suresh_rels = session.run("MATCH (p:Person {name: 'Suresh Valmiki'})-[r]-(other) RETURN type(r) as rel, labels(other) as labels, coalesce(other.name, other.title, other.case_number) as target")
        print("\n   - Relationships for Suresh Valmiki in Neo4j:")
        for r in suresh_rels:
            print(f"     * Suresh Valmiki --[{r['rel']}]--> {r['labels']} ({r['target']})")

    driver.close()
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
