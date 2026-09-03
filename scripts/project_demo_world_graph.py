import os
import sys
import time
import duckdb
import psycopg2
from neo4j import GraphDatabase

CIVIX_ENV = os.environ.get("CIVIX_ENV", "demo")
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

print("==========================================================")
print("CIVIX 2.0 — PHASE 9 COMPLETE DEMO GRAPH PROJECTION ENGINE")
print("==========================================================")
print(f"CIVIX_ENV : {CIVIX_ENV}")
print(f"NEO4J_URI : {NEO4J_URI}")

if CIVIX_ENV != "demo":
    print("[FAIL] HARD ABORT: CIVIX_ENV must strictly be 'demo'.")
    sys.exit(1)

if ":7688" not in NEO4J_URI:
    print(f"[FAIL] HARD ABORT: Target Neo4j URI must strictly be isolated port 7688 (Actual: {NEO4J_URI}).")
    sys.exit(1)

def run_full_projection():
    t_start = time.time()
    
    pg_conn = psycopg2.connect(dbname="civix_demo", user="postgres", password="postgres", host="localhost", port=5432)
    pg_cur = pg_conn.cursor()
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=None if NEO4J_PASSWORD == "" else (NEO4J_USER, NEO4J_PASSWORD))
    
    # 1. Setup Constraints
    with driver.session() as session:
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (o:Organization) REQUIRE o.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (ph:PhoneNumber) REQUIRE ph.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (s:SIM) REQUIRE s.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (d:Device) REQUIRE d.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (fa:FinancialAccount) REQUIRE fa.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (l:Location) REQUIRE l.entity_id IS UNIQUE;")
        session.run("CREATE CONSTRAINT IF NOT EXISTS FOR (c:Case) REQUIRE c.case_id IS UNIQUE;")
        
    print("[PASS] Constraints verified on Demo Neo4j instance.")
    metrics = {}

    # --- Node Projection ---
    print("\n1. Projecting Entity & Case Nodes...")
    
    # Persons
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, display_name, gender, date_of_birth::TEXT FROM civix.person;")
    person_rows = [{"entity_id": r[0], "display_name": r[1], "gender": r[2], "date_of_birth": r[3]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (p:Person {entity_id: row.entity_id}) SET p.display_name = row.display_name, p.gender = row.gender, p.date_of_birth = row.date_of_birth", batch=person_rows)
    metrics["Person"] = len(person_rows)
    print(f"  [PASS] Projected {len(person_rows):,d} Person nodes in {time.time()-t0:.2f}s")

    # Organizations
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, legal_name, org_type FROM civix.organization;")
    org_rows = [{"entity_id": r[0], "legal_name": r[1], "org_type": r[2]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (o:Organization {entity_id: row.entity_id}) SET o.legal_name = row.legal_name, o.org_type = row.org_type", batch=org_rows)
    metrics["Organization"] = len(org_rows)
    print(f"  [PASS] Projected {len(org_rows):,d} Organization nodes in {time.time()-t0:.2f}s")

    # PhoneNumbers
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, msisdn, operator FROM civix.phone_number;")
    ph_rows = [{"entity_id": r[0], "msisdn": r[1], "operator": r[2]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (ph:PhoneNumber {entity_id: row.entity_id}) SET ph.msisdn = row.msisdn, ph.operator = row.operator", batch=ph_rows)
    metrics["PhoneNumber"] = len(ph_rows)
    print(f"  [PASS] Projected {len(ph_rows):,d} PhoneNumber nodes in {time.time()-t0:.2f}s")

    # SIMs
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, iccid FROM civix.sim;")
    sim_rows = [{"entity_id": r[0], "iccid": r[1]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (s:SIM {entity_id: row.entity_id}) SET s.iccid = row.iccid", batch=sim_rows)
    metrics["SIM"] = len(sim_rows)
    print(f"  [PASS] Projected {len(sim_rows):,d} SIM nodes in {time.time()-t0:.2f}s")

    # Devices
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, imei, device_type, manufacturer FROM civix.device;")
    dev_rows = [{"entity_id": r[0], "imei": r[1], "device_type": r[2], "manufacturer": r[3]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (d:Device {entity_id: row.entity_id}) SET d.imei = row.imei, d.device_type = row.device_type, d.manufacturer = row.manufacturer", batch=dev_rows)
    metrics["Device"] = len(dev_rows)
    print(f"  [PASS] Projected {len(dev_rows):,d} Device nodes in {time.time()-t0:.2f}s")

    # FinancialAccounts
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, masked_number, account_type, bank_name FROM civix.financial_account;")
    acc_rows = [{"entity_id": r[0], "masked_number": r[1], "account_type": r[2], "bank_name": r[3]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (fa:FinancialAccount {entity_id: row.entity_id}) SET fa.masked_number = row.masked_number, fa.account_type = row.account_type, fa.bank_name = row.bank_name", batch=acc_rows)
    metrics["FinancialAccount"] = len(acc_rows)
    print(f"  [PASS] Projected {len(acc_rows):,d} FinancialAccount nodes in {time.time()-t0:.2f}s")

    # Locations
    t0 = time.time()
    pg_cur.execute("SELECT entity_id::TEXT, location_name, location_type FROM civix.location;")
    loc_rows = [{"entity_id": r[0], "location_name": r[1], "location_type": r[2]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (l:Location {entity_id: row.entity_id}) SET l.location_name = row.location_name, l.location_type = row.location_type", batch=loc_rows)
    metrics["Location"] = len(loc_rows)
    print(f"  [PASS] Projected {len(loc_rows):,d} Location nodes in {time.time()-t0:.2f}s")

    # Cases
    t0 = time.time()
    pg_cur.execute("SELECT case_id::TEXT, case_number, title, case_type, priority, status FROM civix.investigative_case;")
    case_rows = [{"case_id": r[0], "case_number": r[1], "title": r[2], "case_type": r[3], "priority": r[4], "status": r[5]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("UNWIND $batch AS row MERGE (c:Case {case_id: row.case_id}) SET c.case_number = row.case_number, c.title = row.title, c.case_type = row.case_type, c.priority = row.priority, c.status = row.status", batch=case_rows)
    metrics["Case"] = len(case_rows)
    print(f"  [PASS] Projected {len(case_rows):,d} Case nodes in {time.time()-t0:.2f}s")

    # --- Direct Relationships ---
    print("\n2. Projecting Direct Case Membership & Factual Assertions...")
    
    # Case Entity Roles
    t0 = time.time()
    pg_cur.execute("SELECT case_id::TEXT, entity_id::TEXT, role, role_basis FROM civix.case_entity_role;")
    cer_rows = [{"case_id": r[0], "entity_id": r[1], "role": r[2], "role_basis": r[3]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("""
            UNWIND $batch AS row
            MATCH (c:Case {case_id: row.case_id})
            MATCH (e) WHERE e.entity_id = row.entity_id
            MERGE (c)-[r:HAS_ROLE {role: row.role}]->(e)
            SET r.role_basis = row.role_basis, r.projection_type = 'CASE_MEMBERSHIP', r.aggregation_version = '1.0'
        """, batch=cer_rows)
    metrics["HAS_ROLE"] = len(cer_rows)
    print(f"  [PASS] Projected {len(cer_rows):,d} HAS_ROLE relationships in {time.time()-t0:.2f}s")

    # Assertions
    t0 = time.time()
    pg_cur.execute("SELECT subject_entity_id::TEXT, predicate, object_entity_id::TEXT, epistemic_status, asserted_by::TEXT FROM civix.assertion;")
    ass_rows = [{"subj": r[0], "pred": r[1], "obj": r[2], "status": r[3], "asserted_by": r[4]} for r in pg_cur.fetchall()]
    with driver.session() as session:
        session.run("""
            UNWIND $batch AS row
            MATCH (s) WHERE s.entity_id = row.subj
            MATCH (o) WHERE o.entity_id = row.obj
            MERGE (s)-[r:ASSERTED_RELATIONSHIP {predicate: row.pred}]->(o)
            SET r.epistemic_status = row.status, r.asserted_by = row.asserted_by, r.projection_type = 'FACTUAL_ASSERTION', r.aggregation_version = '1.0'
        """, batch=ass_rows)
    metrics["ASSERTED_RELATIONSHIP"] = len(ass_rows)
    print(f"  [PASS] Projected {len(ass_rows):,d} ASSERTED_RELATIONSHIP relationships in {time.time()-t0:.2f}s")

    # --- Derived Aggregations ---
    print("\n3. Computing & Projecting Derived Graph Edges via DuckDB...")
    duck_con = duckdb.connect(":memory:")
    
    # Derived Telecom (COMMUNICATED_WITH)
    t0 = time.time()
    cdr_path = "demo_world_15k_output/cdrs/**/*.parquet"
    telecom_tuples = duck_con.execute(f"""
        SELECT 
            caller_phone_id::TEXT AS src,
            callee_phone_id::TEXT AS dst,
            COUNT(*)::INT AS source_event_count,
            MIN(timestamp)::TEXT AS source_start_time,
            MAX(timestamp)::TEXT AS source_end_time
        FROM read_parquet('{cdr_path}')
        WHERE caller_phone_id IS NOT NULL AND callee_phone_id IS NOT NULL
        GROUP BY caller_phone_id, callee_phone_id
    """).fetchall()
    
    telecom_batch = [
        {
            "src": r[0], "dst": r[1], "cnt": r[2],
            "st": r[3], "et": r[4]
        }
        for r in telecom_tuples
    ]
    
    # Insert in 2,000-row chunks for optimal Cypher transaction throughput
    chunk_size = 2000
    with driver.session() as session:
        for i in range(0, len(telecom_batch), chunk_size):
            chunk = telecom_batch[i:i+chunk_size]
            session.run("""
                UNWIND $batch AS row
                MATCH (s:PhoneNumber {entity_id: row.src})
                MATCH (d:PhoneNumber {entity_id: row.dst})
                CREATE (s)-[r:COMMUNICATED_WITH {
                    source_event_count: row.cnt,
                    source_start_time: row.st,
                    source_end_time: row.et,
                    projection_type: 'AGGREGATED_TELECOM',
                    aggregation_version: '1.0'
                }]->(d)
            """, batch=chunk)
    metrics["COMMUNICATED_WITH"] = len(telecom_batch)
    print(f"  [PASS] Projected {len(telecom_batch):,d} derived COMMUNICATED_WITH edges in {time.time()-t0:.2f}s")

    # Derived Financial (TRANSFERRED_FUNDS_TO)
    t0 = time.time()
    txn_path = "demo_world_15k_output/transactions/**/*.parquet"
    financial_tuples = duck_con.execute(f"""
        SELECT 
            sender_account_id::TEXT AS src,
            receiver_account_id::TEXT AS dst,
            COUNT(*)::INT AS source_event_count,
            SUM(amount)::DOUBLE AS total_amount,
            MIN(timestamp)::TEXT AS source_start_time,
            MAX(timestamp)::TEXT AS source_end_time
        FROM read_parquet('{txn_path}')
        WHERE sender_account_id IS NOT NULL AND receiver_account_id IS NOT NULL
        GROUP BY sender_account_id, receiver_account_id
    """).fetchall()
    
    financial_batch = [
        {
            "src": r[0], "dst": r[1], "cnt": r[2], "amt": r[3],
            "st": r[4], "et": r[5]
        }
        for r in financial_tuples
    ]
    
    with driver.session() as session:
        for i in range(0, len(financial_batch), chunk_size):
            chunk = financial_batch[i:i+chunk_size]
            session.run("""
                UNWIND $batch AS row
                MATCH (s:FinancialAccount {entity_id: row.src})
                MATCH (d:FinancialAccount {entity_id: row.dst})
                CREATE (s)-[r:TRANSFERRED_FUNDS_TO {
                    source_event_count: row.cnt,
                    total_amount: row.amt,
                    source_start_time: row.st,
                    source_end_time: row.et,
                    projection_type: 'AGGREGATED_FINANCIAL',
                    aggregation_version: '1.0'
                }]->(d)
            """, batch=chunk)
    metrics["TRANSFERRED_FUNDS_TO"] = len(financial_batch)
    print(f"  [PASS] Projected {len(financial_batch):,d} derived TRANSFERRED_FUNDS_TO edges in {time.time()-t0:.2f}s")

    duck_con.close()
    pg_conn.close()
    driver.close()
    
    tot_time = time.time() - t_start
    print(f"\n[PASS] COMPLETE PHASE 9 GRAPH PROJECTION FINISHED IN {tot_time:.2f} SECONDS.")
    return metrics

if __name__ == "__main__":
    run_full_projection()
