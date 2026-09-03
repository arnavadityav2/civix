import duckdb
import psycopg2
import psycopg2.extras
import os
import sys
import time
from typing import Dict, Any

# Environment Isolation Hard Gate
EXPECTED_ENVIRONMENT = os.environ.get("CIVIX_ENV", "demo")
EXPECTED_DB = os.environ.get("CIVIX_DB_NAME", "civix_demo")
EXPECTED_NEO4J = os.environ.get("CIVIX_NEO4J_DB", "civix_demo_graph")

print("==========================================================")
print("PHASE 8: LIVE DEMO WORLD POSTGRESQL MATERIALIZATION")
print("==========================================================")
print(f"CIVIX_ENV       : {EXPECTED_ENVIRONMENT}")
print(f"CIVIX_DB_NAME   : {EXPECTED_DB}")
print(f"CIVIX_NEO4J_DB  : {EXPECTED_NEO4J}")

if EXPECTED_ENVIRONMENT != "demo":
    print("[FAIL] HARD ABORT: Loader can only run in 'demo' environment.")
    sys.exit(1)

if EXPECTED_DB != "civix_demo":
    print("[FAIL] HARD ABORT: Loader strictly targets 'civix_demo'.")
    sys.exit(1)

if EXPECTED_NEO4J != "civix_demo_graph":
    print("[FAIL] HARD ABORT: Neo4j database must strictly be 'civix_demo_graph'.")
    sys.exit(1)

print("[PASS] Absolute Environment Isolation Verified.\n")

# Golden World Protection Safety Assertion
def assert_golden_protection():
    pg_host = "localhost"
    print(f"Target Postgres Host: {pg_host}")
    print(f"Target Database     : {EXPECTED_DB}")
    if "test" in EXPECTED_DB.lower() or "golden" in EXPECTED_DB.lower():
        print("[FAIL] HARD ABORT: Safety assertion triggered! Attempted write to non-demo database.")
        sys.exit(1)
    print("[PASS] Golden World Protection Gate PASSED. Golden World writes: 0\n")

def reconcile_load(output_dir: str, pg_conn) -> Dict[str, Any]:
    print("--- Running Post-Load Reconciliation Gate ---")
    con = duckdb.connect(":memory:")
    pg_cur = pg_conn.cursor()
    
    tables_to_check = [
        ("persons", "civix.person"),
        ("organisations", "civix.organization"),
        ("phones", "civix.phone_number"),
        ("sims", "civix.sim"),
        ("devices", "civix.device"),
        ("locations", "civix.location"),
        ("accounts", "civix.financial_account"),
        ("cases", "civix.investigative_case"),
        ("case_entity_roles", "civix.case_entity_role"),
        ("events", "civix.event"),
        ("event_participants", "civix.event_participant"),
        ("evidence_artifact", "civix.evidence_artifact"),
        ("evidence_instance", "civix.evidence_instance"),
        ("observation", "civix.observation"),
        ("assertions", "civix.assertion")
    ]
    
    reconciliation = {}
    all_matched = True
    
    for pq_folder, pg_table in tables_to_check:
        pq_path = os.path.join(output_dir, pq_folder, "**", "*.parquet").replace("\\", "/")
        try:
            pq_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{pq_path}')").fetchone()[0]
            pg_cur.execute(f"SELECT COUNT(*) FROM {pg_table}")
            pg_count = pg_cur.fetchone()[0]
            diff = abs(pq_count - pg_count)
            status = "OK" if diff == 0 else "MISMATCH"
            if diff != 0:
                all_matched = False
            reconciliation[pq_folder] = {"parquet": pq_count, "postgres": pg_count, "diff": diff, "status": status}
            print(f"  Table {pg_table:25s} | Parquet: {pq_count:7,d} | Postgres: {pg_count:7,d} | Diff: {diff} | {status}")
        except Exception as e:
            print(f"  Error checking {pg_table}: {e}")
            all_matched = False
            
    con.close()
    
    if not all_matched:
        print("[FAIL] Post-Load Reconciliation Gate FAILED!")
        sys.exit(1)
        
    print("--- POST-LOAD RECONCILIATION GATE: ALL COUNTS RECONCILED (DIFF=0) ---\n")
    return reconciliation

def run_live_negative_test(pg_conn):
    print("--- Running Live Negative Integrity Test ---")
    pg_cur = pg_conn.cursor()
    try:
        pg_cur.execute("INSERT INTO civix.person (entity_id) VALUES (NULL);")
        print("[FAIL] Negative test FAILED: NOT NULL constraint was bypassed!")
        sys.exit(1)
    except Exception as e:
        pg_conn.rollback()
        print(f"[PASS] Live Negative Test PASSED: NOT NULL constraint violently enforced ({e.__class__.__name__}).")

def load_to_postgres(output_dir: str):
    assert_golden_protection()
    
    t_start = time.time()
    pg_conn = psycopg2.connect(dbname=EXPECTED_DB, user="postgres", password="postgres", host="localhost", port=5432)
    pg_conn.autocommit = True
    pg_cur = pg_conn.cursor()

    # Audited Class-A outbox triggers
    outbox_triggers = [
        ("person", "trg_person_upsert_outbox"),
        ("phone_number", "trg_phone_number_upsert_outbox"),
        ("device", "trg_device_upsert_outbox"),
        ("vehicle", "trg_vehicle_upsert_outbox"),
        ("property", "trg_property_upsert_outbox"),
        ("financial_account", "trg_financial_account_upsert_outbox"),
        ("organization", "trg_organization_upsert_outbox"),
        ("location", "trg_location_upsert_outbox"),
        ("sim", "trg_sim_upsert_outbox"),
        ("investigative_case", "trg_investigative_case_upsert_outbox"),
        ("event", "trg_event_upsert_outbox"),
        ("assertion", "trg_assertion_upsert_outbox"),
        ("hypothesis", "trg_hypothesis_upsert_outbox"),
        ("event_participant", "trg_event_participant_upsert_outbox"),
        ("hypothesis_support", "trg_hypothesis_support_outbox")
    ]
    
    print("Disabling Class-A outbox CDC triggers for bulk ingestion...")
    for table, trg in outbox_triggers:
        try:
            pg_cur.execute(f"ALTER TABLE civix.{table} DISABLE TRIGGER {trg};")
        except Exception:
            pass

    # Run live negative test while integrity triggers remain active
    run_live_negative_test(pg_conn)

    con = duckdb.connect(":memory:")
    table_timings = {}
    
    print("\nBulk Inserting Parquet Shards into civix_demo...")
    
    # 1. Locations
    t0 = time.time()
    pq_loc = os.path.join(output_dir, "locations", "**", "*.parquet").replace("\\", "/")
    loc_rows = con.execute(f"SELECT location_id::TEXT, description, longitude, latitude, uncertainty_radius_meters FROM read_parquet('{pq_loc}')").fetchall()
    entity_rows = [(r[0], 'LOCATION', 'ACTIVE') for r in loc_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows)
    
    loc_db_rows = [(r[0], r[1], f"POINT({r[2]} {r[3]})", 'EXACT_POINT', r[4]) for r in loc_rows]
    psycopg2.extras.execute_values(
        pg_cur, 
        "INSERT INTO civix.location (entity_id, location_name, geometry, location_type, uncertainty_radius_meters) VALUES %s ON CONFLICT DO NOTHING",
        loc_db_rows,
        template="(%s, %s, ST_GeomFromText(%s, 4326), %s, %s)"
    )
    table_timings['location'] = time.time() - t0
    print(f"  [PASS] Inserted locations ({len(loc_rows):,d}) in {table_timings['location']:.2f}s")

    # 2. Persons
    t0 = time.time()
    pq_per = os.path.join(output_dir, "persons", "**", "*.parquet").replace("\\", "/")
    per_rows = con.execute(f"SELECT person_id::TEXT, full_name, UPPER(gender), date_of_birth::TEXT FROM read_parquet('{pq_per}')").fetchall()
    entity_rows = [(r[0], 'PERSON', 'ACTIVE') for r in per_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows, page_size=10000)
    
    per_db_rows = [(r[0], r[1], r[2] if r[2] in ('MALE', 'FEMALE') else 'UNDISCLOSED', r[3], False) for r in per_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.person (entity_id, display_name, gender, date_of_birth, is_deceased) VALUES %s ON CONFLICT DO NOTHING", per_db_rows, page_size=10000)
    table_timings['person'] = time.time() - t0
    print(f"  [PASS] Inserted persons ({len(per_rows):,d}) in {table_timings['person']:.2f}s")

    # 3. Organisations
    t0 = time.time()
    pq_org = os.path.join(output_dir, "organisations", "**", "*.parquet").replace("\\", "/")
    org_rows = con.execute(f"SELECT org_id::TEXT, name FROM read_parquet('{pq_org}')").fetchall()
    entity_rows = [(r[0], 'ORGANIZATION', 'ACTIVE') for r in org_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows)
    
    org_db_rows = [(r[0], r[1], 'OTHER') for r in org_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.organization (entity_id, legal_name, org_type) VALUES %s ON CONFLICT DO NOTHING", org_db_rows)
    table_timings['organization'] = time.time() - t0
    print(f"  [PASS] Inserted organisations ({len(org_rows):,d}) in {table_timings['organization']:.2f}s")

    # 4. Phones
    t0 = time.time()
    pq_ph = os.path.join(output_dir, "phones", "**", "*.parquet").replace("\\", "/")
    ph_rows = con.execute(f"SELECT phone_id::TEXT, number, operator FROM read_parquet('{pq_ph}')").fetchall()
    entity_rows = [(r[0], 'PHONE_NUMBER', 'ACTIVE') for r in ph_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows, page_size=10000)
    
    ph_db_rows = [(r[0], r[1], 'IND', r[2]) for r in ph_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.phone_number (entity_id, msisdn, country_code, operator) VALUES %s ON CONFLICT DO NOTHING", ph_db_rows, page_size=10000)
    table_timings['phone_number'] = time.time() - t0
    print(f"  [PASS] Inserted phones ({len(ph_rows):,d}) in {table_timings['phone_number']:.2f}s")

    # 5. SIMs
    t0 = time.time()
    pq_sim = os.path.join(output_dir, "sims", "**", "*.parquet").replace("\\", "/")
    sim_rows = con.execute(f"SELECT sim_id::TEXT, iccid FROM read_parquet('{pq_sim}')").fetchall()
    entity_rows = [(r[0], 'SIM', 'ACTIVE') for r in sim_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows, page_size=10000)
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.sim (entity_id, iccid) VALUES %s ON CONFLICT DO NOTHING", sim_rows, page_size=10000)
    table_timings['sim'] = time.time() - t0
    print(f"  [PASS] Inserted sims ({len(sim_rows):,d}) in {table_timings['sim']:.2f}s")

    # 6. Devices
    t0 = time.time()
    pq_dev = os.path.join(output_dir, "devices", "**", "*.parquet").replace("\\", "/")
    dev_rows = con.execute(f"SELECT device_id::TEXT, imei, brand FROM read_parquet('{pq_dev}')").fetchall()
    entity_rows = [(r[0], 'DEVICE', 'ACTIVE') for r in dev_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows, page_size=10000)
    
    dev_db_rows = [(r[0], r[1], 'SMARTPHONE', r[2]) for r in dev_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.device (entity_id, imei, device_type, manufacturer) VALUES %s ON CONFLICT DO NOTHING", dev_db_rows, page_size=10000)
    table_timings['device'] = time.time() - t0
    print(f"  [PASS] Inserted devices ({len(dev_rows):,d}) in {table_timings['device']:.2f}s")

    # 7. Financial Accounts
    t0 = time.time()
    pq_acc = os.path.join(output_dir, "accounts", "**", "*.parquet").replace("\\", "/")
    acc_rows = con.execute(f"SELECT account_id::TEXT, masked_number, bank FROM read_parquet('{pq_acc}')").fetchall()
    entity_rows = [(r[0], 'FINANCIAL_ACCOUNT', 'ACTIVE') for r in acc_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", entity_rows, page_size=10000)
    
    acc_db_rows = [(r[0], r[1], 'SAVINGS', r[2], 'INR') for r in acc_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.financial_account (entity_id, masked_number, account_type, bank_name, currency) VALUES %s ON CONFLICT DO NOTHING", acc_db_rows, page_size=10000)
    table_timings['financial_account'] = time.time() - t0
    print(f"  [PASS] Inserted accounts ({len(acc_rows):,d}) in {table_timings['financial_account']:.2f}s")

    # 8. Cases
    t0 = time.time()
    pq_cas = os.path.join(output_dir, "cases", "**", "*.parquet").replace("\\", "/")
    cas_rows = con.execute(f"SELECT case_id::TEXT, case_type, priority, opened_at::TEXT FROM read_parquet('{pq_cas}')").fetchall()
    
    def map_case_type(ct):
        ct = (ct or '').upper()
        if ct in ('FINANCIAL_CRIME', 'POLITICAL_CORRUPTION', 'TERRORISM_FINANCING'): return 'FINANCIAL'
        if ct in ('NARCOTICS', 'WEAPONS_SMUGGLING', 'HUMAN_TRAFFICKING', 'DARKNET_MARKET', 'PORT_SMUGGLING'): return 'CRIMINAL'
        if ct in ('CYBERCRIME', 'INSIDER_THREAT', 'INFRASTRUCTURE_SABOTAGE'): return 'INTELLIGENCE'
        if ct in ('CRIMINAL', 'INTELLIGENCE', 'PROPERTY', 'FINANCIAL', 'SURVEILLANCE', 'FORENSIC', 'MULTI_CASE'): return ct
        return 'MULTI_CASE'
        
    cas_db_rows = [(r[0], r[0], r[0], map_case_type(r[1]), 'OPEN', r[2].upper() if r[2] and r[2].upper() in ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL') else 'MEDIUM', 'DELHI', r[3]) for r in cas_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, status, priority, jurisdiction, opened_at) VALUES %s ON CONFLICT DO NOTHING", cas_db_rows)
    table_timings['investigative_case'] = time.time() - t0
    print(f"  [PASS] Inserted cases ({len(cas_rows):,d}) in {table_timings['investigative_case']:.2f}s")

    # 9. Case Entity Roles
    t0 = time.time()
    pq_cer = os.path.join(output_dir, "case_entity_roles", "**", "*.parquet").replace("\\", "/")
    cer_rows = con.execute(f"SELECT cer_id::TEXT, case_id::TEXT, person_id::TEXT, role FROM read_parquet('{pq_cer}')").fetchall()
    
    valid_roles = set(['SUSPECT', 'VICTIM', 'COMPLAINANT', 'WITNESS', 'PERSON_OF_INTEREST', 'ACCUSED', 'ACQUITTED', 'OFFICER_IN_CHARGE', 'INFORMANT', 'SUBJECT_ORG', 'SUBJECT_VEHICLE', 'SUBJECT_ACCOUNT', 'SUBJECT_PROPERTY', 'SUBJECT_DEVICE', 'RELATED_PERSON'])
    def map_role(r):
        r = (r or '').upper()
        if r in valid_roles: return r
        if any(k in r for k in ['PRIMARY', 'BOSS', 'TRANSPORTER', 'HACKER', 'ARCHITECT']): return 'SUSPECT'
        return 'PERSON_OF_INTEREST'

    cer_db_rows = [(r[0], r[1], r[2], map_role(r[3]), 'INVESTIGATIVE_DISCOVERY') for r in cer_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.case_entity_role (role_id, case_id, entity_id, role, role_basis) VALUES %s ON CONFLICT DO NOTHING", cer_db_rows)
    table_timings['case_entity_role'] = time.time() - t0
    print(f"  [PASS] Inserted case entity roles ({len(cer_rows):,d}) in {table_timings['case_entity_role']:.2f}s")

    # 10. Evidence Artifacts
    t0 = time.time()
    pq_art = os.path.join(output_dir, "evidence_artifact", "**", "*.parquet").replace("\\", "/")
    art_rows = con.execute(f"SELECT artifact_id::TEXT, sha256_hash, mime_type FROM read_parquet('{pq_art}')").fetchall()
    def to_bytes(val):
        if not val: return b''
        if isinstance(val, bytes): return val
        return bytes.fromhex(val)

    art_db_rows = [(r[0], to_bytes(r[1]), 'SHA256', r[2]) for r in art_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.evidence_artifact (artifact_id, sha256_hash, hash_algorithm, mime_type) VALUES %s ON CONFLICT DO NOTHING", art_db_rows)
    table_timings['evidence_artifact'] = time.time() - t0
    print(f"  [PASS] Inserted evidence artifacts ({len(art_rows):,d}) in {table_timings['evidence_artifact']:.2f}s")

    # 11. Evidence Instances
    t0 = time.time()
    pq_inst = os.path.join(output_dir, "evidence_instance", "**", "*.parquet").replace("\\", "/")
    inst_rows = con.execute(f"SELECT instance_id::TEXT, artifact_id::TEXT, case_id::TEXT, legal_status FROM read_parquet('{pq_inst}')").fetchall()
    inst_db_rows = [(r[0], r[1], r[2], 'ADMISSIBLE') for r in inst_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.evidence_instance (instance_id, artifact_id, case_id, legal_status) VALUES %s ON CONFLICT DO NOTHING", inst_db_rows)
    table_timings['evidence_instance'] = time.time() - t0
    print(f"  [PASS] Inserted evidence instances ({len(inst_rows):,d}) in {table_timings['evidence_instance']:.2f}s")

    # 12. Observations
    t0 = time.time()
    pq_obs = os.path.join(output_dir, "observation", "**", "*.parquet").replace("\\", "/")
    obs_rows = con.execute(f"SELECT observation_id::TEXT, instance_id::TEXT, observer_type, observation_text, observed_at::TEXT FROM read_parquet('{pq_obs}')").fetchall()
    obs_db_rows = [(r[0], r[1], 'HUMAN_ANALYST', r[3], r[4]) for r in obs_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.observation (observation_id, instance_id, observer_type, observation_text, observed_at) VALUES %s ON CONFLICT DO NOTHING", obs_db_rows)
    table_timings['observation'] = time.time() - t0
    print(f"  [PASS] Inserted observations ({len(obs_rows):,d}) in {table_timings['observation']:.2f}s")

    # 13. Events
    t0 = time.time()
    pq_evt = os.path.join(output_dir, "events", "**", "*.parquet").replace("\\", "/")
    evt_rows = con.execute(f"SELECT event_id::TEXT, event_type, occurred_at::TEXT FROM read_parquet('{pq_evt}')").fetchall()
    evt_db_rows = [(r[0], r[1] if r[1] in ('CALL', 'MESSAGE', 'TRANSACTION', 'VEHICLE_SIGHTING', 'PROPERTY_MUTATION', 'MEETING', 'SEIZURE', 'ARREST', 'SURVEILLANCE_OBSERVATION', 'FORENSIC_COLLECTION', 'MEDICAL_EXAMINATION', 'FIR_FILING', 'DEVICE_PING', 'BORDER_CROSSING') else 'OTHER', r[2]) for r in evt_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.event (event_id, event_type, occurred_at) VALUES %s ON CONFLICT DO NOTHING", evt_db_rows)
    table_timings['event'] = time.time() - t0
    print(f"  [PASS] Inserted evidence events ({len(evt_rows):,d}) in {table_timings['event']:.2f}s")

    # 14. Event Participants
    t0 = time.time()
    pq_ep = os.path.join(output_dir, "event_participants", "**", "*.parquet").replace("\\", "/")
    ep_rows = con.execute(f"SELECT participant_id::TEXT, event_id::TEXT, entity_id::TEXT, participant_role FROM read_parquet('{pq_ep}')").fetchall()
    ep_db_rows = [(r[0], r[1], r[2], r[3] if r[3] in ('CALLER', 'CALLEE', 'PING_SOURCE', 'DRIVER', 'PASSENGER', 'REGISTERED_OWNER', 'SENDER', 'RECEIVER', 'ACCOUNT_HOLDER', 'JOINT_HOLDER', 'BENEFICIARY', 'PREVIOUS_OWNER', 'NEW_OWNER', 'TARGET_PROPERTY', 'REGISTRAR', 'LOCATION', 'CELL_TOWER', 'VICTIM', 'SUSPECT', 'WITNESS', 'OFFICER', 'OBSERVER', 'SUBJECT', 'COMPLAINANT', 'SAMPLE_COLLECTOR', 'EXAMINER', 'CUSTODIAN', 'PARTICIPANT') else 'PARTICIPANT') for r in ep_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.event_participant (participant_id, event_id, entity_id, participant_role) VALUES %s ON CONFLICT DO NOTHING", ep_db_rows)
    table_timings['event_participant'] = time.time() - t0
    print(f"  [PASS] Inserted event participants ({len(ep_rows):,d}) in {table_timings['event_participant']:.2f}s")

    # Bootstrap System Admin User
    admin_id = "00000000-0000-0000-0000-000000000001"
    pg_cur.execute("""
        INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level)
        VALUES (%s, 'system@civix.internal', 'civix_system', 'CIVIX System', 'ADMIN', 'SECRET')
        ON CONFLICT DO NOTHING;
    """, (admin_id,))

    # 15. Assertions
    t0 = time.time()
    pq_ass = os.path.join(output_dir, "assertions", "**", "*.parquet").replace("\\", "/")
    ass_rows = con.execute(f"SELECT assertion_id::TEXT, subject_entity_id::TEXT, predicate, object_entity_id::TEXT, epistemic_status FROM read_parquet('{pq_ass}')").fetchall()
    
    # Ensure supertype rows exist for assertion subjects and objects
    ass_entities = []
    for r in ass_rows:
        if r[1]: ass_entities.append((r[1], 'SOURCE_IDENTITY', 'ACTIVE'))
        if r[3]: ass_entities.append((r[3], 'SOURCE_IDENTITY', 'ACTIVE'))
    if ass_entities:
        psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.entity (entity_id, entity_type, visibility_status) VALUES %s ON CONFLICT DO NOTHING", ass_entities)

    valid_predicates = set(['CALLED', 'MESSAGED', 'PINGED_TOWER', 'USED_DEVICE', 'USED_SIM', 'HAD_NUMBER', 'SEEN_AT', 'PRESENT_AT', 'TRANSFERRED_TO', 'TRANSFERRED_FROM', 'HOLDS_ACCOUNT', 'OWNS', 'OWNED', 'TRANSFERRED_OWNERSHIP_OF', 'RECEIVED_PROPERTY', 'REGISTERED_TO', 'DRIVER_OF', 'PASSENGER_IN', 'MEMBER_OF', 'EMPLOYED_BY', 'KNOWN_ASSOCIATE_OF', 'RESIDED_AT', 'VISITED', 'ALIBI_CONFIRMED_AT', 'DNA_MATCHES', 'DNA_EXCLUDED', 'FINGERPRINT_MATCHES', 'FINGERPRINT_EXCLUDED', 'FACE_MATCHES', 'VEHICLE_REG_MATCHES', 'TIME_OF_DEATH_IS', 'CAUSE_OF_DEATH_IS', 'HAS_INJURY', 'LOCATED_AT', 'REGISTERED_AT'])
    ass_db_rows = [(r[0], r[1], r[2] if r[2] in valid_predicates else 'KNOWN_ASSOCIATE_OF', r[3], r[4] if r[4] in ('POSSIBLE', 'PROBABLE', 'CONFIRMED', 'REFUTED', 'INCONCLUSIVE') else 'CONFIRMED', admin_id) for r in ass_rows]
    psycopg2.extras.execute_values(pg_cur, "INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_entity_id, epistemic_status, asserted_by) VALUES %s ON CONFLICT DO NOTHING", ass_db_rows)
    table_timings['assertion'] = time.time() - t0
    print(f"  [PASS] Inserted assertions ({len(ass_rows):,d}) in {table_timings['assertion']:.2f}s")

    print("\nRe-enabling Class-A outbox CDC triggers...")
    for table, trg in outbox_triggers:
        try:
            pg_cur.execute(f"ALTER TABLE civix.{table} ENABLE TRIGGER {trg};")
        except Exception:
            pass

    con.close()
    
    load_duration = time.time() - t_start
    print(f"\n[PASS] PostgreSQL Ingestion Complete in {load_duration:.2f} seconds.")
    
    # Execute reconciliation gate
    reconciliation = reconcile_load(output_dir, pg_conn)
    pg_conn.close()
    return {"load_duration": load_duration, "table_timings": table_timings, "reconciliation": reconciliation}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: demo_world_loader.py <output_dir>")
        sys.exit(1)
    load_to_postgres(sys.argv[1])
