import asyncio
import asyncpg
from neo4j import GraphDatabase
import json
import sys

PG_DSN = "postgresql://postgres:postgres@localhost:5433/civix_test"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "password")

async def run_full_audit():
    pg_conn = await asyncpg.connect(PG_DSN)
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

    report = {}

    # -------------------------------------------------------------
    # PART 1: CASE INVENTORY
    # -------------------------------------------------------------
    pg_cases = await pg_conn.fetch("""
        SELECT case_id, case_number, title, status, priority, case_type
        FROM civix.investigative_case
        ORDER BY created_at ASC
    """)
    
    cases_inventory = []
    with neo4j_driver.session() as session:
        for c in pg_cases:
            cid = str(c['case_id'])
            res = session.run("MATCH (c:Case {case_id: $cid}) RETURN c", cid=cid)
            rec = res.single()
            has_neo4j = rec is not None

            res_neighbors = session.run("MATCH (c:Case {case_id: $cid})-[r]-(n) RETURN count(DISTINCT n) as cnt", cid=cid)
            neighbors_cnt = res_neighbors.single()["cnt"] if has_neo4j else 0

            cases_inventory.append({
                "case_id": cid,
                "case_number": c['case_number'],
                "title": c['title'],
                "status": c['status'],
                "priority": c['priority'],
                "case_type": c['case_type'],
                "neo4j_exists": has_neo4j,
                "direct_graph_neighbors": neighbors_cnt
            })
    report["part1_cases_inventory"] = cases_inventory

    # -------------------------------------------------------------
    # PART 2 & 3: CASE-2026-0142 END-TO-END TRACE & NLP DIAGNOSTIC
    # -------------------------------------------------------------
    target_case = await pg_conn.fetchrow("SELECT * FROM civix.investigative_case WHERE case_number = 'CASE-2026-0142'")
    if not target_case:
        target_case = await pg_conn.fetchrow("SELECT * FROM civix.investigative_case WHERE case_id = '530831f5-4032-4533-be70-8a78bb5a7435'")
    
    if target_case:
        t_cid = target_case['case_id']
        t_cid_str = str(t_cid)
        
        # Counts in PG
        # Evidence artifacts linked via instances
        cnt_artifacts = await pg_conn.fetchval("""
            SELECT count(DISTINCT artifact_id) FROM civix.evidence_instance WHERE case_id = $1
        """, t_cid)
        cnt_instances = await pg_conn.fetchval("SELECT count(*) FROM civix.evidence_instance WHERE case_id = $1", t_cid)
        
        cnt_obs = await pg_conn.fetchval("""
            SELECT count(o.*) FROM civix.observation o
            JOIN civix.evidence_instance ei ON o.instance_id = ei.instance_id
            WHERE ei.case_id = $1
        """, t_cid)

        # Check if extraction table exists
        has_extraction = await pg_conn.fetchval("SELECT to_regclass('civix.extraction')")
        cnt_ext = 0
        cnt_rel_ext = 0
        ext_types = []
        if has_extraction:
            cnt_ext = await pg_conn.fetchval("""
                SELECT count(e.*) FROM civix.extraction e
                JOIN civix.observation o ON e.observation_id = o.observation_id
                JOIN civix.evidence_instance ei ON o.instance_id = ei.instance_id
                WHERE ei.case_id = $1
            """, t_cid)
            
            cnt_rel_ext = await pg_conn.fetchval("""
                SELECT count(e.*) FROM civix.extraction e
                JOIN civix.observation o ON e.observation_id = o.observation_id
                JOIN civix.evidence_instance ei ON o.instance_id = ei.instance_id
                WHERE ei.case_id = $1 AND (e.extraction_type LIKE '%RELATION%' OR e.extraction_type LIKE '%REL%')
            """, t_cid)

            ext_types = await pg_conn.fetch("""
                SELECT e.extraction_type, count(*) as count FROM civix.extraction e
                JOIN civix.observation o ON e.observation_id = o.observation_id
                JOIN civix.evidence_instance ei ON o.instance_id = ei.instance_id
                WHERE ei.case_id = $1
                GROUP BY e.extraction_type
            """, t_cid)
        
        # Assertions
        cnt_assertions = await pg_conn.fetchval("""
            SELECT count(*) FROM civix.assertion WHERE $1 = ANY(authorized_case_ids)
        """, t_cid)

        # Total assertions in entire DB
        cnt_total_assertions = await pg_conn.fetchval("SELECT count(*) FROM civix.assertion")

        # Entity counts via case_entity_role
        cnt_persons = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%PERSON%' OR role::text LIKE '%SUBJECT%' OR role::text LIKE '%SUSPECT%'", t_cid)
        cnt_orgs = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%ORGANIZATION%' OR role::text LIKE '%COMPANY%'", t_cid)
        cnt_vehicles = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%VEHICLE%'", t_cid)
        cnt_locations = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%LOCATION%'", t_cid)
        cnt_events = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%EVENT%'", t_cid)
        cnt_accounts = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%ACCOUNT%'", t_cid)
        cnt_devices = await pg_conn.fetchval("SELECT count(DISTINCT entity_id) FROM civix.case_entity_role WHERE case_id = $1 AND role::text LIKE '%PHONE%' OR role::text LIKE '%DEVICE%'", t_cid)
        cnt_case_roles = await pg_conn.fetchval("SELECT count(*) FROM civix.case_entity_role WHERE case_id = $1", t_cid)
        
        cnt_outbox_total = await pg_conn.fetchval("SELECT count(*) FROM civix.outbox")
        cnt_outbox_consumed = await pg_conn.fetchval("SELECT count(*) FROM civix.outbox WHERE consumed_at IS NOT NULL")
        cnt_outbox_failed = await pg_conn.fetchval("SELECT count(*) FROM civix.outbox WHERE error_status IS NOT NULL")

        with neo4j_driver.session() as session:
            r1 = session.run("MATCH (c:Case {case_id: $cid})-[r]-(n) RETURN count(DISTINCT n) as nodes, count(DISTINCT r) as rels", cid=t_cid_str).single()
            r2 = session.run("MATCH path = (c:Case {case_id: $cid})-[*1..2]-(n) UNWIND nodes(path) as nd UNWIND relationships(path) as rl RETURN count(DISTINCT nd) as nodes, count(DISTINCT rl) as rels", cid=t_cid_str).single()
            
            neo4j_1hop_nodes = r1["nodes"] if r1 else 0
            neo4j_1hop_rels = r1["rels"] if r1 else 0
            neo4j_2hop_nodes = r2["nodes"] if r2 else 0
            neo4j_2hop_rels = r2["rels"] if r2 else 0

        report["part2_trace"] = {
            "case_id": t_cid_str,
            "case_number": target_case['case_number'],
            "title": target_case['title'],
            "evidence_artifacts": cnt_artifacts,
            "evidence_instances": cnt_instances,
            "observations": cnt_obs,
            "extractions": cnt_ext,
            "relationship_extractions": cnt_rel_ext,
            "extraction_types_breakdown": [dict(r) for r in ext_types],
            "assertions_for_case": cnt_assertions,
            "total_assertions_in_db": cnt_total_assertions,
            "persons_in_roles": cnt_persons,
            "organizations_in_roles": cnt_orgs,
            "vehicles_in_roles": cnt_vehicles,
            "locations_in_roles": cnt_locations,
            "events_in_roles": cnt_events,
            "financial_accounts_in_roles": cnt_accounts,
            "phones_devices_in_roles": cnt_devices,
            "case_entity_roles_count": cnt_case_roles,
            "cdc_outbox_total": cnt_outbox_total,
            "cdc_outbox_consumed": cnt_outbox_consumed,
            "cdc_outbox_failed": cnt_outbox_failed,
            "neo4j_1hop_nodes": neo4j_1hop_nodes,
            "neo4j_1hop_rels": neo4j_1hop_rels,
            "neo4j_2hop_nodes": neo4j_2hop_nodes,
            "neo4j_2hop_rels": neo4j_2hop_rels
        }

    # -------------------------------------------------------------
    # PART 4: CASE ASSOCIATION MECHANISM IN PG vs NEO4J
    # -------------------------------------------------------------
    roles_sample = await pg_conn.fetch("SELECT * FROM civix.case_entity_role LIMIT 5")
    report["part4_pg_roles_sample"] = [dict(r) for r in roles_sample]

    access_sample = await pg_conn.fetch("SELECT * FROM civix.case_access LIMIT 5")
    report["part4_pg_access_sample"] = [dict(r) for r in access_sample]

    # -------------------------------------------------------------
    # PART 5: NEO4J CASE CONNECTIVITY FOR ALL CASES
    # -------------------------------------------------------------
    neo4j_case_connectivity = []
    with neo4j_driver.session() as session:
        n_cases = session.run("MATCH (c:Case) RETURN c.case_id as cid, c.case_number as cnum, c.title as title")
        for rec in n_cases:
            cid = rec["cid"]
            cnum = rec["cnum"]
            r1 = session.run("MATCH (c:Case {case_id: $cid})-[r]-(n) RETURN count(DISTINCT n) as nodes, count(DISTINCT r) as rels", cid=cid).single()
            r2 = session.run("MATCH path = (c:Case {case_id: $cid})-[*1..2]-(n) UNWIND nodes(path) as nd UNWIND relationships(path) as rl RETURN count(DISTINCT nd) as nodes, count(DISTINCT rl) as rels", cid=cid).single()
            neo4j_case_connectivity.append({
                "case_id": cid,
                "case_number": cnum,
                "hop1_nodes": r1["nodes"],
                "hop1_rels": r1["rels"],
                "hop2_nodes": r2["nodes"],
                "hop2_rels": r2["rels"]
            })
    report["part5_case_connectivity"] = neo4j_case_connectivity

    # -------------------------------------------------------------
    # PART 6: GLOBAL NEO4J GRAPH INVENTORY (REACHABLE VS UNREACHABLE)
    # -------------------------------------------------------------
    with neo4j_driver.session() as session:
        tot_nodes = session.run("MATCH (n) RETURN count(n) as cnt").single()["cnt"]
        tot_rels = session.run("MATCH ()-[r]->() RETURN count(r) as cnt").single()["cnt"]
        
        labels_res = session.run("CALL db.labels() YIELD label RETURN label")
        labels = [r["label"] for r in labels_res]
        
        node_stats = []
        for lbl in labels:
            tot_lbl = session.run(f"MATCH (n:`{lbl}`) RETURN count(n) as cnt").single()["cnt"]
            reach_lbl = session.run(f"MATCH (c:Case)-[*0..5]-(n:`{lbl}`) RETURN count(DISTINCT n) as cnt").single()["cnt"]
            node_stats.append({
                "label": lbl,
                "total": tot_lbl,
                "case_reachable": reach_lbl,
                "unreachable": tot_lbl - reach_lbl
            })
            
        rel_types_res = session.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType")
        rel_types = [r["relationshipType"] for r in rel_types_res]
        
        rel_stats = []
        for rt in rel_types:
            tot_rt = session.run(f"MATCH ()-[r:`{rt}`]->() RETURN count(r) as cnt").single()["cnt"]
            reach_rt = session.run(f"MATCH path = (c:Case)-[*0..5]-(n) UNWIND relationships(path) as r WHERE type(r) = $rt RETURN count(DISTINCT r) as cnt", rt=rt).single()["cnt"]
            rel_stats.append({
                "type": rt,
                "total": tot_rt,
                "case_reachable": reach_rt,
                "unreachable": tot_rt - reach_rt
            })
            
    report["part6_global_inventory"] = {
        "total_nodes": tot_nodes,
        "total_rels": tot_rels,
        "node_types": node_stats,
        "relationship_types": rel_stats
    }

    # -------------------------------------------------------------
    # PART 7: STRANDED ENTITY SAMPLES
    # -------------------------------------------------------------
    with neo4j_driver.session() as session:
        stranded_samples = {}
        target_labels = ["Person", "Identity", "Organization", "Vehicle", "Location", "Event", "FinancialAccount", "PhoneNumber", "Assertion"]
        for lbl in target_labels:
            res = session.run(f"""
                MATCH (n:`{lbl}`)
                OPTIONAL MATCH (c:Case)-[*1..5]-(n)
                WITH n, count(c) as case_conn
                WHERE case_conn = 0
                MATCH (n)-[r]-(m)
                RETURN elementId(n) as id, labels(n) as labels, keys(n) as props, count(r) as total_rels, collect(DISTINCT type(r)) as rel_types
                LIMIT 3
            """)
            stranded_samples[lbl] = [dict(r) for r in res]
    report["part7_stranded_samples"] = stranded_samples

    # -------------------------------------------------------------
    # PART 10: C0/C4 PLANTED RELATIONSHIPS TRACE
    # -------------------------------------------------------------
    planted_pairs = [
        ("Vikram Singh", "Global Exports Pvt Ltd"),
        ("Vikram Singh", "White Maruti Dzire"),
        ("Vikram Singh", "Black Toyota Fortuner"),
        ("Neha Gupta", "Apex Shell Consultants"),
        ("Neha Gupta", "Global Exports Pvt Ltd"),
        ("Vikram Singh", "Neha Gupta"),
        ("Apex Shell Consultants", "Global Exports Pvt Ltd"),
        ("Vikram Singh", "Rahul Sharma"),
        ("Neha Gupta", "Drug Trafficking Cartel")
    ]

    pair_audit = []
    for e1, e2 in planted_pairs:
        assertions_pg = await pg_conn.fetch("""
            SELECT a.assertion_id, a.predicate, a.authorized_case_ids
            FROM civix.assertion a
        """)
        
        with neo4j_driver.session() as session:
            n_res = session.run("""
                MATCH (n)-[r]-(m)
                WHERE (coalesce(n.primary_name, n.name, n.value, n.registration_number, '') ILIKE $e1 
                       AND coalesce(m.primary_name, m.name, m.value, m.registration_number, '') ILIKE $e2)
                   OR (coalesce(n.primary_name, n.name, n.value, n.registration_number, '') ILIKE $e2 
                       AND coalesce(m.primary_name, m.name, m.value, m.registration_number, '') ILIKE $e1)
                RETURN type(r) as rtype, labels(n) as nlabels, labels(m) as mlabels,
                       coalesce(n.case_id, n.authorized_case_ids) as ncase, coalesce(m.case_id, m.authorized_case_ids) as mcase
            """, e1=f"%{e1}%", e2=f"%{e2}%")
            neo4j_rels = [dict(r) for r in n_res]

        pair_audit.append({
            "pair": f"{e1} <-> {e2}",
            "neo4j_relationships_count": len(neo4j_rels),
            "neo4j_relationships": neo4j_rels
        })
    report["part10_planted_pairs"] = pair_audit

    await pg_conn.close()
    neo4j_driver.close()

    with open("scratch/audit_report_raw.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    print("Full audit output saved to scratch/audit_report_raw.json successfully!")

if __name__ == "__main__":
    asyncio.run(run_full_audit())
