import asyncio
import asyncpg
from neo4j import GraphDatabase
import json
import sys

PG_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")

async def run_audit():
    pg_conn = await asyncpg.connect(PG_DSN)
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    
    print("=== PART 1: CASE INVENTORY ===")
    pg_cases = await pg_conn.fetch("""
        SELECT case_id, case_number, title, status, priority, case_type
        FROM cases
        ORDER BY created_at ASC
    """)
    
    with neo4j_driver.session() as session:
        for c in pg_cases:
            cid = str(c['case_id'])
            # Check Neo4j Case node
            res = session.run("MATCH (c:Case {case_id: $cid}) RETURN c", cid=cid)
            rec = res.single()
            has_neo4j = rec is not None
            
            # Check direct graph neighbors in Neo4j
            res_neighbors = session.run("MATCH (c:Case {case_id: $cid})-[r]-(n) RETURN count(n) as cnt", cid=cid)
            neighbors_cnt = res_neighbors.single()["cnt"] if has_neo4j else 0
            
            print(f"Case: {c['case_number']} | PG ID: {cid} | Title: {c['title']} | Status: {c['status']} | Priority: {c['priority']} | Type: {c['case_type']} | In Neo4j: {has_neo4j} | Direct Neighbors: {neighbors_cnt}")

    print("\n=== PART 2: CASE-2026-0142 END-TO-END TRACE ===")
    # Target case
    target_case = await pg_conn.fetchrow("SELECT * FROM cases WHERE case_number = 'CASE-2026-0142'")
    if not target_case:
        # Fallback by ID if number differs
        target_case = await pg_conn.fetchrow("SELECT * FROM cases WHERE case_id = '530831f5-4032-4533-be70-8a78bb5a7435'")
    
    if target_case:
        t_cid = str(target_case['case_id'])
        print(f"Target Case found: {target_case['case_number']} (ID: {t_cid})")
        
        # 1. Case count
        cnt_case = 1
        
        # 2. Evidence artifacts
        cnt_artifacts = await pg_conn.fetchval("SELECT count(*) FROM evidence_artifacts WHERE case_id = $1", target_case['case_id'])
        
        # 3. Evidence instances
        cnt_instances = await pg_conn.fetchval("SELECT count(*) FROM evidence_instances WHERE case_id = $1", target_case['case_id'])
        
        # 4. Observations
        cnt_obs = await pg_conn.fetchval("""
            SELECT count(o.*) FROM observations o
            JOIN evidence_instances ei ON o.evidence_instance_id = ei.instance_id
            WHERE ei.case_id = $1
        """, target_case['case_id'])
        
        # 5. Extractions
        cnt_ext = await pg_conn.fetchval("""
            SELECT count(e.*) FROM extractions e
            JOIN observations o ON e.observation_id = o.observation_id
            JOIN evidence_instances ei ON o.evidence_instance_id = ei.instance_id
            WHERE ei.case_id = $1
        """, target_case['case_id'])
        
        # 6. Relationship extractions
        cnt_rel_ext = await pg_conn.fetchval("""
            SELECT count(e.*) FROM extractions e
            JOIN observations o ON e.observation_id = o.observation_id
            JOIN evidence_instances ei ON o.evidence_instance_id = ei.instance_id
            WHERE ei.case_id = $1 AND e.extraction_type LIKE '%RELATION%' OR e.extraction_type LIKE '%REL%'
        """, target_case['case_id'])
        
        # 7. Assertions
        cnt_assertions = await pg_conn.fetchval("SELECT count(*) FROM assertions WHERE case_id = $1", target_case['case_id'])
        
        # 8. Source identities
        cnt_identities = await pg_conn.fetchval("""
            SELECT count(DISTINCT identity_id) FROM case_entity_roles WHERE case_id = $1 AND identity_id IS NOT NULL
        """, target_case['case_id'])
        
        # 9. Persons
        cnt_persons = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type = 'PERSON'
        """, target_case['case_id'])
        
        # 10. Organizations
        cnt_orgs = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type = 'ORGANIZATION'
        """, target_case['case_id'])
        
        # 11. Vehicles
        cnt_vehicles = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type = 'VEHICLE'
        """, target_case['case_id'])
        
        # 12. Locations
        cnt_locations = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type = 'LOCATION'
        """, target_case['case_id'])
        
        # 13. Events
        cnt_events = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type = 'EVENT'
        """, target_case['case_id'])
        
        # 14. Financial accounts
        cnt_accounts = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type = 'FINANCIAL_ACCOUNT'
        """, target_case['case_id'])
        
        # 15. Phones / devices
        cnt_devices = await pg_conn.fetchval("""
            SELECT count(DISTINCT entity_id) FROM case_entity_roles WHERE case_id = $1 AND entity_type IN ('PHONE_NUMBER', 'DEVICE', 'SIM')
        """, target_case['case_id'])
        
        # 16. Case / entity associations total
        cnt_case_entity_roles = await pg_conn.fetchval("SELECT count(*) FROM case_entity_roles WHERE case_id = $1", target_case['case_id'])
        
        # 17. Outbox events
        cnt_outbox = await pg_conn.fetchval("SELECT count(*) FROM cdc_outbox")
        # 18. Consumed outbox
        cnt_outbox_consumed = await pg_conn.fetchval("SELECT count(*) FROM cdc_outbox WHERE status = 'CONSUMED' OR status = 'PROCESSED'")
        # 19. Failed outbox
        cnt_outbox_failed = await pg_conn.fetchval("SELECT count(*) FROM cdc_outbox WHERE status IN ('FAILED', 'PERMANENT_FAILURE')")
        
        with neo4j_driver.session() as session:
            # 20. Neo4j nodes connected to case
            res_nodes = session.run("""
                MATCH (c:Case {case_id: $cid})-[*1..2]-(n)
                RETURN count(DISTINCT n) as cnt
            """, cid=t_cid)
            neo4j_nodes_cnt = res_nodes.single()["cnt"]
            
            # 21. Neo4j relationships
            res_rels = session.run("""
                MATCH path = (c:Case {case_id: $cid})-[*1..2]-(n)
                UNWIND relationships(path) as r
                RETURN count(DISTINCT r) as cnt
            """, cid=t_cid)
            neo4j_rels_cnt = res_rels.single()["cnt"]
            
        print(f"""
        1. Case: {cnt_case}
        2. Evidence Artifacts: {cnt_artifacts}
        3. Evidence Instances: {cnt_instances}
        4. Observations: {cnt_obs}
        5. Extractions: {cnt_ext}
        6. Relationship Extractions: {cnt_rel_ext}
        7. Assertions: {cnt_assertions}
        8. Source Identities: {cnt_identities}
        9. Persons: {cnt_persons}
        10. Organizations: {cnt_orgs}
        11. Vehicles: {cnt_vehicles}
        12. Locations: {cnt_locations}
        13. Events: {cnt_events}
        14. Financial Accounts: {cnt_accounts}
        15. Phones/Devices: {cnt_devices}
        16. Case Entity Roles: {cnt_case_entity_roles}
        17. Total Outbox Events: {cnt_outbox}
        18. Consumed Outbox: {cnt_outbox_consumed}
        19. Failed Outbox: {cnt_outbox_failed}
        20. Neo4j Reachable Nodes (depth 2): {neo4j_nodes_cnt}
        21. Neo4j Reachable Rels (depth 2): {neo4j_rels_cnt}
        """)

    await pg_conn.close()
    neo4j_driver.close()

if __name__ == "__main__":
    asyncio.run(run_audit())
