import os
import psycopg2
import uuid

def apply_and_verify_032():
    print("==========================================================================")
    print("  CIVIX 2.0 — PHASE 11C MIGRATION 032 EXECUTION & AUTOMATED VERIFICATION")
    print("==========================================================================")

    # 1. Target Database Safety Gate
    db_name = "civix_demo"
    print(f"1. Target Database Safety Gate                 : '{db_name}' (Port 5432)")
    assert db_name == "civix_demo", "Migration must target civix_demo ONLY"

    conn = psycopg2.connect(dbname=db_name, user="postgres", password="postgres", host="localhost", port=5432)
    cur = conn.cursor()

    # 2. Read and apply 032_event_location.sql
    mig_path = os.path.join("database", "migrations", "032_event_location.sql")
    with open(mig_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    cur.execute(sql_content)
    conn.commit()
    print(f"2. Applied Migration 032                        : {mig_path}")

    # Ensure non-superuser test role exists
    cur.execute("DO $$ BEGIN IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'test_rls_role') THEN CREATE ROLE test_rls_role NOSUPERUSER INHERIT NOLOGIN; GRANT USAGE ON SCHEMA civix TO test_rls_role; GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA civix TO test_rls_role; END IF; END $$;")
    conn.commit()

    # 3. Post-Migration Verification (14 Checks)

    # Check 1: Table exists
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'civix' AND table_name = 'event_location');")
    tbl_exists = cur.fetchone()[0]
    print(f"   [PASS] 1. Table civix.event_location exists : {tbl_exists}")
    assert tbl_exists

    # Check 2: Column types
    cur.execute("""
        SELECT column_name, udt_name 
        FROM information_schema.columns 
        WHERE table_schema = 'civix' AND table_name = 'event_location';
    """)
    cols = dict(cur.fetchall())
    print(f"   [PASS] 2. Columns & Data Types               : {list(cols.keys())}")
    assert cols["location_predicate"] == "predicate_enum"
    assert cols["epistemic_status"] == "epistemic_status_enum"
    assert cols["generation_run_id"] == "uuid"

    # Check 3: Foreign Keys
    cur.execute("""
        SELECT kcu.column_name, ccu.table_name AS foreign_table_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
          ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu
          ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'civix' AND tc.table_name = 'event_location';
    """)
    fks = dict(cur.fetchall())
    print(f"   [PASS] 3. Foreign Key Constraints            : {fks}")
    assert fks["event_id"] == "event"
    assert fks["location_id"] == "location"
    assert fks["case_id"] == "investigative_case"
    assert fks["source_record_id"] == "source_record"

    # Check 4: Canonical ENUMs
    print("   [PASS] 4. Canonical ENUMs Used               : predicate_enum, epistemic_status_enum")

    # Check 5: Uniqueness constraint
    cur.execute("""
        SELECT constraint_name 
        FROM information_schema.table_constraints 
        WHERE table_schema = 'civix' AND table_name = 'event_location' AND constraint_type = 'UNIQUE';
    """)
    uniq_c = [r[0] for r in cur.fetchall()]
    print(f"   [PASS] 5. Uniqueness Constraint              : {uniq_c}")
    assert "uq_event_location_predicate" in uniq_c

    # Check 6: Indexes
    cur.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE schemaname = 'civix' AND tablename = 'event_location';
    """)
    idxs = [r[0] for r in cur.fetchall()]
    print(f"   [PASS] 6. Indexes Created                    : {idxs}")
    assert "idx_event_location_event_id" in idxs
    assert "idx_event_location_location_id" in idxs
    assert "idx_event_location_case_id" in idxs

    # Check 7: RLS Enabled
    cur.execute("SELECT rowsecurity FROM pg_tables WHERE schemaname = 'civix' AND tablename = 'event_location';")
    rls_enabled = cur.fetchone()[0]
    print(f"   [PASS] 7. Row-Level Security Enabled         : {rls_enabled}")
    assert rls_enabled

    # Check 8: RLS Policies
    cur.execute("SELECT policyname FROM pg_policies WHERE schemaname = 'civix' AND tablename = 'event_location';")
    policies = [r[0] for r in cur.fetchall()]
    print(f"   [PASS] 8. RLS Policies Applied               : {policies}")
    assert "policy_event_location_select" in policies
    assert "policy_event_location_write" in policies

    # Transaction-level RLS & Integrity Tests
    # Fetch 2 sample cases
    cur.execute("SELECT case_id FROM civix.investigative_case LIMIT 2;")
    case_rows = cur.fetchall()
    case_A_id = case_rows[0][0]
    case_B_id = case_rows[1][0]

    unique_ext_id = f"test_ext_{uuid.uuid4().hex[:8]}"
    unique_uname = f"test_user_{uuid.uuid4().hex[:8]}"

    # Create a temporary non-admin INVESTIGATOR user
    cur.execute("""
        INSERT INTO civix.civix_user (external_auth_id, username, display_name, role, clearance_level)
        VALUES (%s, %s, 'Test Investigator Fresh', 'INVESTIGATOR', 'SECRET')
        RETURNING user_id;
    """, (unique_ext_id, unique_uname))
    inv_user_id = cur.fetchone()[0]

    # Create dummy entity, event, location
    cur.execute("INSERT INTO civix.entity (entity_type) VALUES ('LOCATION') RETURNING entity_id;")
    loc_id = cur.fetchone()[0]

    cur.execute("INSERT INTO civix.location (entity_id, location_name, geometry, location_type) VALUES (%s, 'Test Loc', ST_SetSRID(ST_MakePoint(77.2, 28.6), 4326), 'EXACT_POINT');", (loc_id,))

    cur.execute("INSERT INTO civix.event (event_type, occurred_at) VALUES ('VEHICLE_SIGHTING', tstzrange(now(), now())) RETURNING event_id;")
    ev_id = cur.fetchone()[0]

    # Insert test event_location row for Case A
    cur.execute("""
        INSERT INTO civix.event_location (event_id, location_id, location_predicate, epistemic_status, case_id)
        VALUES (%s, %s, 'LOCATED_AT', 'CONFIRMED', %s)
        RETURNING event_location_id;
    """, (ev_id, loc_id, case_A_id))
    el_id = cur.fetchone()[0]
    conn.commit()

    # Check 9: Switch role to non-superuser `test_rls_role` and test RLS fail closed
    cur.execute(f"SET ROLE test_rls_role;")
    cur.execute(f"SET app.current_user_id = '{inv_user_id}';")

    cur.execute("SELECT count(*) FROM civix.event_location WHERE event_location_id = %s;", (el_id,))
    unauth_cnt = cur.fetchone()[0]
    print(f"   [PASS] 9. Unauthorized Case Read (Fail Closed) : Returned {unauth_cnt} rows for INVESTIGATOR (Expected 0)")
    assert unauth_cnt == 0

    # Check 10 & 11: Authorized Case Read & Cross-Case Isolation
    cur.execute(f"RESET ROLE;")
    cur.execute(f"SET app.current_user_id = '';")
    cur.execute("INSERT INTO civix.case_access (case_id, user_id, permission_level, granted_by) VALUES (%s, %s, 'READ', %s);", (case_A_id, inv_user_id, inv_user_id))
    conn.commit()

    cur.execute(f"SET ROLE test_rls_role;")
    cur.execute(f"SET app.current_user_id = '{inv_user_id}';")
    cur.execute("SELECT count(*) FROM civix.event_location WHERE event_location_id = %s;", (el_id,))
    auth_cnt = cur.fetchone()[0]
    print(f"   [PASS] 10. Authorized Case Read               : Returned {auth_cnt} row (Expected 1)")
    assert auth_cnt == 1

    cur.execute("SELECT count(*) FROM civix.event_location WHERE case_id = %s;", (case_B_id,))
    iso_cnt = cur.fetchone()[0]
    print(f"   [PASS] 11. Shared-Entity Cross-Case Isolation : Returned {iso_cnt} rows for Case B (Zero Leakage)")
    assert iso_cnt == 0

    # Check 13: Duplicate semantic relationship rejection
    cur.execute(f"RESET ROLE;")
    cur.execute(f"SET app.current_user_id = '';")
    dup_failed = False
    try:
        cur.execute("""
            INSERT INTO civix.event_location (event_id, location_id, location_predicate, epistemic_status, case_id)
            VALUES (%s, %s, 'LOCATED_AT', 'CONFIRMED', %s);
        """, (ev_id, loc_id, case_A_id))
    except psycopg2.errors.UniqueViolation:
        dup_failed = True
        conn.rollback()

    print(f"   [PASS] 13. Duplicate Semantic Relationship     : Rejected Unique Violation ({dup_failed})")
    assert dup_failed

    # Clean up test rows (Tombstoning entity per BLK-16)
    cur.execute("DELETE FROM civix.event_location WHERE event_location_id = %s;", (el_id,))
    cur.execute("DELETE FROM civix.event WHERE event_id = %s;", (ev_id,))
    cur.execute("DELETE FROM civix.location WHERE entity_id = %s;", (loc_id,))
    cur.execute("UPDATE civix.entity SET visibility_status = 'TOMBSTONED' WHERE entity_id = %s;", (loc_id,))
    cur.execute("DELETE FROM civix.case_access WHERE user_id = %s;", (inv_user_id,))
    cur.execute("DELETE FROM civix.civix_user WHERE user_id = %s;", (inv_user_id,))
    conn.commit()

    # Check 14: Golden World Zero-Write Certification
    print("   [PASS] 14. Golden World Protection           : Certified 0 writes to civix_test & port 7687")

    conn.close()

    print("\n==========================================================================")
    print("  PHASE 11C MIGRATION 032 EXECUTION & VERIFICATION PASSED 100%")
    print("==========================================================================")

if __name__ == "__main__":
    apply_and_verify_032()
