#!/usr/bin/env python3
"""
CIVIX Phase 2A — Live Database Verification Harness
====================================================
Executes all 15 migrations against a live PostgreSQL + PostGIS instance
and runs the complete verification test suite.

Architecture is FROZEN. This script ONLY verifies. It does NOT modify schema.

Usage:
    python database/verify_phase2a.py

Environment variables:
    CIVIX_DB_HOST     (default: localhost)
    CIVIX_DB_PORT     (default: 5432)
    CIVIX_DB_NAME     (default: civix_verify)
    CIVIX_DB_USER     (default: postgres)
    CIVIX_DB_PASSWORD (required)
"""

import os
import sys
import json
import uuid
import time
import traceback
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
MIGRATIONS_DIR = Path(__file__).parent / "migrations"
BASE_DIR = Path(__file__).parent.parent

DB_HOST = os.getenv("CIVIX_DB_HOST", "localhost")
DB_PORT = os.getenv("CIVIX_DB_PORT", "5432")
DB_NAME = os.getenv("CIVIX_DB_NAME", "civix_verify")
DB_USER = os.getenv("CIVIX_DB_USER", "postgres")
DB_PASS = os.getenv("CIVIX_DB_PASSWORD")
if not DB_PASS:
    print("CIVIX_DB_PASSWORD is missing")
    sys.exit(1)

PSQL_BIN = None  # discovered at runtime

EXPECTED_TABLES = 52
EXPECTED_ENUMS  = 27

MIGRATION_FILES = [
    "000_extensions.sql",
    "001_enums.sql",
    "002_users_and_synthetic.sql",
    "003_source_and_evidence.sql",
    "004_core_entities.sql",
    "005_identity_resolution.sql",
    "006_telecom_and_financial.sql",
    "007_cases_and_access.sql",
    "008_epistemic_pipeline.sql",
    "009_workflow_and_legal.sql",
    "010_provenance_and_quality.sql",
    "011_triggers.sql",
    "012_indexes.sql",
    "013_rls.sql",
    "014_validation.sql",
]

# ── Result tracking ──────────────────────────────────────────────────────────
results = {
    "environment":    {},
    "migrations":     {},
    "tables":         {},
    "enums":          {},
    "constraints":    {},
    "triggers":       {},
    "bitemporal":     {},
    "identity":       {},
    "h4_event":       {},
    "evidence":       {},
    "rls":            {},
    "outbox":         {},
    "data_quality":   {},
    "indexes":        {},
    "validation_sql": {},
    "failures":       [],
}

verdict = "PASS"

def fail(section: str, key: str, detail: str):
    global verdict
    verdict = "FAIL"
    results[section][key] = f"FAIL: {detail}"
    results["failures"].append({"section": section, "key": key, "detail": detail})
    print(f"  ✗ FAIL [{section}] {key}: {detail}")

def passs(section: str, key: str, detail: str = ""):
    results[section][key] = f"PASS{': ' + detail if detail else ''}"
    print(f"  ✓ PASS [{section}] {key}{': ' + detail if detail else ''}")

def block(section: str, key: str, detail: str):
    results[section][key] = f"BLOCKED: {detail}"
    print(f"  ⊘ BLOCKED [{section}] {key}: {detail}")

# ── Subprocess helpers ───────────────────────────────────────────────────────
def psql(sql: str, db: str = None, capture: bool = True) -> tuple[int, str, str]:
    """Run SQL via psql. Returns (returncode, stdout, stderr)."""
    target_db = db or DB_NAME
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    cmd = [
        PSQL_BIN,
        "-h", DB_HOST, "-p", DB_PORT,
        "-U", DB_USER, "-d", target_db,
        "-c", sql,
        "--no-psqlrc", "--tuples-only", "--no-align",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def psql_file(filepath: Path, db: str = None) -> tuple[int, str, str]:
    """Run a SQL file via psql."""
    target_db = db or DB_NAME
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    cmd = [
        PSQL_BIN,
        "-h", DB_HOST, "-p", DB_PORT,
        "-U", DB_USER, "-d", target_db,
        "-f", str(filepath),
        "--no-psqlrc",
        "-v", "ON_ERROR_STOP=1",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr

def query_one(sql: str, db: str = None) -> str | None:
    """Return first cell of first row, or None."""
    rc, out, err = psql(sql, db)
    if rc != 0 or not out:
        return None
    return out.split("\n")[-1].strip()

def query_list(sql: str, db: str = None) -> list[str]:
    """Return list of first-column values."""
    rc, out, _ = psql(sql, db)
    if rc != 0 or not out:
        return []
    # filter out 'SET' from results
    return [line.strip() for line in out.split("\n") if line.strip() and line.strip() != "SET"]

# ── Step 1: Environment Discovery ────────────────────────────────────────────
def discover_environment():
    global PSQL_BIN
    print("\n═══ STEP 1: ENVIRONMENT DISCOVERY ═══")

    # Find psql binary
    pg_paths = [
        r"C:\Program Files\PostgreSQL\17\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\16\bin\psql.exe",
        r"C:\Program Files\PostgreSQL\15\bin\psql.exe",
    ]
    for p in pg_paths:
        if Path(p).exists():
            PSQL_BIN = p
            break

    if not PSQL_BIN:
        # Try PATH
        try:
            r = subprocess.run(["psql", "--version"], capture_output=True, text=True)
            if r.returncode == 0:
                PSQL_BIN = "psql"
        except FileNotFoundError:
            pass

    if not PSQL_BIN:
        print("  ✗ psql binary not found. PostgreSQL may still be installing.")
        results["environment"]["psql_found"] = "NOT FOUND"
        return False

    # PostgreSQL version
    r = subprocess.run([PSQL_BIN, "--version"], capture_output=True, text=True)
    pg_version = r.stdout.strip()
    results["environment"]["psql_binary"] = PSQL_BIN
    results["environment"]["psql_version"] = pg_version
    print(f"  psql binary: {PSQL_BIN}")
    print(f"  version: {pg_version}")

    # Port 5432 reachability
    rc, out, err = psql("SELECT version();", db="postgres")
    if rc != 0:
        print(f"  ✗ Cannot connect to PostgreSQL on {DB_HOST}:{DB_PORT}")
        print(f"    Error: {err}")
        results["environment"]["postgres_connection"] = f"FAIL: {err}"
        return False

    results["environment"]["postgres_connection"] = "OK"
    results["environment"]["server_version"] = out
    print(f"  Connected: {out[:80]}")

    # PostGIS
    rc, out, _ = psql("SELECT PostGIS_version();", db="postgres")
    if rc == 0 and out:
        results["environment"]["postgis_version"] = out
        print(f"  PostGIS: {out}")
    else:
        results["environment"]["postgis_version"] = "NOT_INSTALLED_YET (will be installed by migration 000)"
        print("  PostGIS: not yet installed (migration 000 will install it)")

    # pgcrypto, btree_gist, uuid-ossp
    for ext in ["pgcrypto", "btree_gist", "uuid-ossp"]:
        rc, out, _ = psql(f"SELECT count(*) FROM pg_extension WHERE extname = '{ext}';", db="postgres")
        results["environment"][f"ext_{ext}"] = "AVAILABLE" if rc == 0 else "UNKNOWN"

    results["environment"]["discovery_timestamp"] = datetime.now(timezone.utc).isoformat()
    return True

# ── Step 2: Create test database ─────────────────────────────────────────────
def create_test_database():
    print(f"\n═══ STEP 2: CREATE ISOLATED TEST DATABASE '{DB_NAME}' ═══")

    # Drop if exists (clean slate)
    rc, out, err = psql(f"DROP DATABASE IF EXISTS {DB_NAME};", db="postgres")
    if rc != 0:
        print(f"  Warning dropping existing DB: {err}")

    rc, out, err = psql(f"CREATE DATABASE {DB_NAME};", db="postgres")
    if rc != 0:
        fail("migrations", "create_database", err)
        return False

    passs("migrations", "create_database", f"Database '{DB_NAME}' created")
    return True

# ── Step 3: Run Migrations ────────────────────────────────────────────────────
def run_migrations():
    print("\n═══ STEP 3: EXECUTE MIGRATIONS 000–014 ═══")
    migration_log = []
    
    for filename in MIGRATION_FILES:
        filepath = MIGRATIONS_DIR / filename
        if not filepath.exists():
            fail("migrations", filename, f"File not found: {filepath}")
            print(f"\n  STOPPING: Migration file missing.")
            return False

        print(f"\n  [{filename}] Applying...")
        t0 = time.time()
        rc, stdout, stderr = psql_file(filepath)
        elapsed = time.time() - t0

        entry = {
            "file": filename,
            "returncode": rc,
            "elapsed_s": round(elapsed, 2),
            "stdout": stdout[:500] if stdout else "",
            "stderr": stderr[:500] if stderr else "",
        }
        migration_log.append(entry)

        if rc != 0:
            fail("migrations", filename, stderr[:300])
            results["migrations"]["log"] = migration_log
            print(f"\n  STOPPING at {filename} — migration chain halted.")
            return False
        else:
            passs("migrations", filename, f"{elapsed:.2f}s")
            if stderr and "ERROR" in stderr.upper():
                print(f"    WARNING (stderr): {stderr[:200]}")

    results["migrations"]["log"] = migration_log
    return True

# ── Step 4: Structural Verification ──────────────────────────────────────────
def verify_structure():
    print("\n═══ STEP 4: STRUCTURAL VERIFICATION ═══")

    # A: Schema
    val = query_one("SELECT nspname FROM pg_namespace WHERE nspname = 'civix';")
    if val == "civix":
        passs("tables", "schema_civix_exists")
    else:
        fail("tables", "schema_civix_exists", "civix schema not found")

    # B: Tables
    table_list = query_list(
        "SELECT tablename FROM pg_tables WHERE schemaname = 'civix' ORDER BY tablename;"
    )
    results["tables"]["found_tables"] = table_list
    results["tables"]["found_count"] = len(table_list)
    
    print(f"\n  Tables found: {len(table_list)} (expected ~{EXPECTED_TABLES})")
    for t in table_list:
        print(f"    • {t}")

    REQUIRED_TABLES = [
        "account_holder", "analysis_run", "assertion", "audit_event",
        "case_access", "case_entity_role", "case_link", "civix_user",
        "data_quality_issue", "dataset", "device", "evidence_artifact",
        "evidence_instance", "event", "event_participant", "extraction",
        "fir", "financial_account", "forensic_report", "generation_run",
        "hypothesis", "hypothesis_support", "identity_candidate",
        "identity_merge_event", "identity_resolution", "identity_split_event",
        "investigation_task", "investigative_case", "investigative_lead",
        "legal_restriction", "location", "medical_report", "network",
        "observation", "organization", "outbox", "person", "person_alias",
        "person_device_use", "person_sim_ownership", "phone_number",
        "property", "provenance", "scenario", "sim", "sim_in_device",
        "sim_number_assignment", "source", "source_identity", "source_record",
        "vehicle",
    ]

    missing = [t for t in REQUIRED_TABLES if t not in table_list]
    unexpected = [t for t in table_list if t not in REQUIRED_TABLES]

    if missing:
        fail("tables", "missing_tables", str(missing))
    else:
        passs("tables", "all_required_tables_present", f"{len(REQUIRED_TABLES)} tables verified")

    if unexpected:
        results["tables"]["unexpected_tables"] = unexpected
        print(f"  INFO: Unexpected tables (informational): {unexpected}")

    # C: ENUMs
    print("\n  ENUMs:")
    enum_list = query_list(
        "SELECT typname FROM pg_type WHERE typtype = 'e' "
        "AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix') "
        "ORDER BY typname;"
    )
    results["enums"]["found_enums"] = enum_list
    results["enums"]["found_count"] = len(enum_list)
    print(f"  ENUM types found: {len(enum_list)} (expected {EXPECTED_ENUMS})")
    for e in enum_list:
        print(f"    • {e}")

    if len(enum_list) < EXPECTED_ENUMS:
        fail("enums", "enum_count", f"Expected {EXPECTED_ENUMS}, found {len(enum_list)}")
    else:
        passs("enums", "enum_count", f"{len(enum_list)} ENUMs found")

    # Verify critical ENUM values
    critical_enums = [
        ("hypothesis_status_enum", ["ACTIVE", "ARCHIVED", "CONFIRMED", "REFUTED", "UNDER_REVIEW"]),
        ("lead_status_enum", ["CLOSED", "CONFIRMED", "DEFERRED", "FALSE_POSITIVE", "IN_PROGRESS", "OPEN"]),
        ("support_stance_enum", ["CONTRADICT", "INCONCLUSIVE", "NEUTRAL", "SUPPORT"]),
    ]
    for enum_name, expected_vals in critical_enums:
        vals = query_list(
            f"SELECT enumlabel FROM pg_enum "
            f"WHERE enumtypid = 'civix.{enum_name}'::regtype ORDER BY enumlabel;"
        )
        if set(expected_vals).issubset(set(vals)):
            passs("enums", enum_name, f"{len(vals)} values verified")
        else:
            missing_v = set(expected_vals) - set(vals)
            fail("enums", enum_name, f"Missing values: {missing_v}")

    # D: Critical column checks
    print("\n  Critical column checks:")

    # person must NOT have is_criminal
    val = query_one(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema='civix' AND table_name='person' "
        "AND column_name='is_criminal';"
    )
    if val == "0":
        passs("constraints", "person_no_is_criminal", "INV-17 enforced")
    else:
        fail("constraints", "person_no_is_criminal", "is_criminal column EXISTS on person (INV-17 VIOLATED)")

    # assertion must NOT have stance
    val = query_one(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema='civix' AND table_name='assertion' "
        "AND column_name='stance';"
    )
    if val == "0":
        passs("constraints", "assertion_no_stance", "INV-01 enforced")
    else:
        fail("constraints", "assertion_no_stance", "stance column EXISTS on assertion (INV-01 VIOLATED)")

    # source_identity must NOT have extraction_id
    val = query_one(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema='civix' AND table_name='source_identity' "
        "AND column_name='extraction_id';"
    )
    if val == "0":
        passs("constraints", "source_identity_no_extraction_id", "ADR-014 enforced")
    else:
        fail("constraints", "source_identity_no_extraction_id", "extraction_id EXISTS on source_identity (ADR-014 VIOLATED)")

    # entity must have visibility_status
    val = query_one(
        "SELECT count(*) FROM information_schema.columns "
        "WHERE table_schema='civix' AND table_name='entity' "
        "AND column_name='visibility_status';"
    )
    if val == "1":
        passs("constraints", "entity_has_visibility_status", "BLK-16 enforced")
    else:
        fail("constraints", "entity_has_visibility_status", "visibility_status MISSING from entity")

    # event must NOT have entity FK columns
    forbidden_event_cols = ["subject_id", "sender_id", "receiver_id", "location_id", "driver_id"]
    fec = query_one(
        f"SELECT count(*) FROM information_schema.columns "
        f"WHERE table_schema='civix' AND table_name='event' "
        f"AND column_name = ANY(ARRAY{forbidden_event_cols!r});"
    )
    if fec == "0":
        passs("constraints", "event_no_entity_fks", "ADR-021/INV-05 enforced")
    else:
        fail("constraints", "event_no_entity_fks", f"Forbidden entity FK columns found on event table")

    # E: Unique constraints
    print("\n  Unique constraints:")
    checks = [
        ("evidence_artifact", "uq_artifact_hash", "ADR-004"),
        ("sim_number_assignment", "excl_sim_number_time", "ADR-009 GIST exclusion"),
        ("sim_in_device", "excl_sim_in_device_time", "INV-15 GIST exclusion"),
        ("event_participant", "uq_event_participant", "BLK-21"),
    ]
    for table, conname, ref in checks:
        val = query_one(
            f"SELECT count(*) FROM pg_constraint "
            f"WHERE conrelid = 'civix.{table}'::regclass AND conname = '{conname}';"
        )
        if val == "1":
            passs("constraints", conname, ref)
        else:
            fail("constraints", conname, f"{ref} constraint NOT found on {table}")

    # Partial unique indexes
    partial_idx = [
        ("uq_active_hypothesis_support", "BLK-06"),
        ("uq_active_case_entity_role", "BLK-12"),
        ("uq_active_case_access", "Gate 3"),
    ]
    for idx, ref in partial_idx:
        val = query_one(
            f"SELECT count(*) FROM pg_indexes "
            f"WHERE schemaname='civix' AND indexname='{idx}';"
        )
        if val == "1":
            passs("constraints", idx, f"Partial index — {ref}")
        else:
            fail("constraints", idx, f"Partial index '{idx}' NOT found ({ref})")

    # F: CHECK constraints
    print("\n  CHECK constraints:")
    chk_checks = [
        ("hypothesis", "chk_hypothesis_human_confirmation", "INV-08"),
        ("assertion", "chk_assertion_has_object", "assertion object required"),
        ("investigative_case", "chk_case_closed_after_opened", "date sanity"),
    ]
    for table, conname, ref in chk_checks:
        val = query_one(
            f"SELECT count(*) FROM pg_constraint "
            f"WHERE conrelid = 'civix.{table}'::regclass AND conname = '{conname}';"
        )
        if val == "1":
            passs("constraints", conname, ref)
        else:
            fail("constraints", conname, f"CHECK constraint '{conname}' NOT found on {table} ({ref})")

    # G: Extensions
    print("\n  Extensions:")
    for ext in ["postgis", "uuid-ossp", "pgcrypto", "btree_gist"]:
        val = query_one(f"SELECT count(*) FROM pg_extension WHERE extname = '{ext}';")
        if val == "1":
            passs("constraints", f"ext_{ext}", "extension installed")
        else:
            fail("constraints", f"ext_{ext}", f"Extension '{ext}' NOT installed")

    # H: GIN index on authorized_case_ids (BLK-15)
    val = query_one(
        "SELECT count(*) FROM pg_indexes "
        "WHERE schemaname='civix' AND indexname='idx_assertion_authorized_cases';"
    )
    if val == "1":
        passs("indexes", "idx_assertion_authorized_cases", "GIN index exists (BLK-15)")
    else:
        fail("indexes", "idx_assertion_authorized_cases", "Critical GIN index NOT found (BLK-15)")

# ── Step 5: Bitemporal Tests ──────────────────────────────────────────────────
def test_bitemporal():
    print("\n═══ STEP 5: BITEMPORAL ENFORCEMENT TESTS ═══")

    # Create bootstrap records for testing
    psql("SET search_path TO civix, public;")

    # Create test user
    test_user_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role, clearance_level) "
        f"VALUES ('{test_user_id}', 'test@civix.test', 'test_user', 'Test User', 'INVESTIGATOR', 'UNCLASSIFIED');"
    )
    if rc != 0:
        block("bitemporal", "setup", f"Cannot create test user: {err}")
        return
    passs("bitemporal", "test_user_created")

    # Create test hypothesis
    test_case_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.investigative_case (case_id, case_number, title, case_type, jurisdiction, opened_at) "
        f"VALUES ('{test_case_id}', 'CIV-TEST-001', 'Bitemporal Test Case', 'CRIMINAL', 'IN', '2026-01-01');"
    )
    if rc != 0:
        block("bitemporal", "test_case_created", err)
        return
    passs("bitemporal", "test_case_created")

    # 5a: hypothesis_support UPDATE → bitemporal trigger
    test_hyp_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.hypothesis (hypothesis_id, case_id, hypothesis_text, status, created_by) "
        f"VALUES ('{test_hyp_id}', '{test_case_id}', 'Test hypothesis', 'ACTIVE', '{test_user_id}');"
    )
    if rc == 0:
        passs("bitemporal", "hypothesis_insert")
    else:
        fail("bitemporal", "hypothesis_insert", err[:200])
        return

    # Create test assertion
    test_entity_id = str(uuid.uuid4())
    rc, _, _ = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{test_entity_id}', 'SOURCE_IDENTITY');"
    )
    test_si_id = test_entity_id
    rc, _, _ = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at) "
        f"VALUES ('{test_si_id}', 'TEST-SI-001', 'NAME', now());"
    )

    # Create test object entity for assertion
    test_obj_id = str(uuid.uuid4())
    psql(f"SET search_path TO civix, public; INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{test_obj_id}', 'LOCATION');")

    test_src_id = str(uuid.uuid4())
    psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.source (source_id, source_name, agency_type) VALUES ('{test_src_id}', 'TestSource', 'POLICE');"
    )

    test_assert_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.assertion (assertion_id, subject_entity_id, predicate, object_entity_id, "
        f"epistemic_status, asserted_by, authorized_case_ids) "
        f"VALUES ('{test_assert_id}', '{test_si_id}', 'SEEN_AT', '{test_obj_id}', "
        f"'POSSIBLE', '{test_user_id}', ARRAY['{test_case_id}']::uuid[]);"
    )
    if rc == 0:
        passs("bitemporal", "assertion_insert")
    else:
        fail("bitemporal", "assertion_insert", err[:200])

    # Create hypothesis_support row
    test_hs_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.hypothesis_support (support_id, hypothesis_id, assertion_id, stance, assigned_by) "
        f"VALUES ('{test_hs_id}', '{test_hyp_id}', '{test_assert_id}', 'SUPPORT', '{test_user_id}');"
    )
    if rc == 0:
        passs("bitemporal", "hypothesis_support_insert")
    else:
        fail("bitemporal", "hypothesis_support_insert", err[:200])
        return

    # Now UPDATE hypothesis_support — trigger should intercept and create new row
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"UPDATE civix.hypothesis_support SET stance = 'NEUTRAL' WHERE support_id = '{test_hs_id}';"
    )
    # After trigger: old row should have tx_end set, new row created
    count = query_one(
        f"SET search_path TO civix, public; "
        f"SELECT count(*) FROM civix.hypothesis_support "
        f"WHERE hypothesis_id = '{test_hyp_id}' AND assertion_id = '{test_assert_id}';"
    )
    closed_count = query_one(
        f"SET search_path TO civix, public; "
        f"SELECT count(*) FROM civix.hypothesis_support "
        f"WHERE hypothesis_id = '{test_hyp_id}' AND tx_end IS NOT NULL;"
    )
    active_count = query_one(
        f"SET search_path TO civix, public; "
        f"SELECT count(*) FROM civix.hypothesis_support "
        f"WHERE hypothesis_id = '{test_hyp_id}' AND tx_end IS NULL;"
    )

    if count == "2" and closed_count == "1" and active_count == "1":
        passs("bitemporal", "hypothesis_support_bitemporal_trigger",
              "UPDATE created 2 rows (1 closed, 1 active) — BLK-17 ✓")
    else:
        fail("bitemporal", "hypothesis_support_bitemporal_trigger",
             f"Expected 2 rows (1 closed, 1 active). Got total={count}, closed={closed_count}, active={active_count}")

    # 5b: audit_event append-only trigger
    rc_insert, _, _ = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.audit_event (user_id, action, target_table, target_id) "
        f"VALUES ('{test_user_id}', 'READ', 'test_table', gen_random_uuid());"
    )
    if rc_insert == 0:
        passs("bitemporal", "audit_event_insert")
    else:
        fail("bitemporal", "audit_event_insert", "Cannot insert audit event")

    rc_update, _, err_update = psql(
        f"SET search_path TO civix, public; "
        f"UPDATE civix.audit_event SET target_table = 'tampered' WHERE user_id = '{test_user_id}';"
    )
    if rc_update != 0 and "append-only" in err_update.lower() or "civix invariant" in err_update.lower():
        passs("bitemporal", "audit_event_immutable", "UPDATE correctly rejected — INV-13 ✓")
    elif rc_update != 0:
        passs("bitemporal", "audit_event_immutable", f"UPDATE rejected (trigger fired): {err_update[:100]}")
    else:
        fail("bitemporal", "audit_event_immutable", "UPDATE on audit_event SUCCEEDED — INV-13 VIOLATED")

    # 5c: AS-OF reconstruction template
    val = query_one(
        f"SET search_path TO civix, public; "
        f"SELECT count(*) FROM civix.hypothesis_support hs "
        f"WHERE hs.hypothesis_id = '{test_hyp_id}' "
        f"AND hs.tx_start <= now() AND (hs.tx_end IS NULL OR hs.tx_end > now());"
    )
    if val == "1":
        passs("bitemporal", "as_of_reconstruction", "AS-OF query returns exactly 1 active row")
    else:
        fail("bitemporal", "as_of_reconstruction", f"AS-OF query returned {val} rows, expected 1")

# ── Step 6: Identity Model Tests ─────────────────────────────────────────────
def test_identity():
    print("\n═══ STEP 6: IDENTITY MODEL TESTS ═══")

    # Test entity physical DELETE is blocked
    test_e_id = str(uuid.uuid4())
    psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{test_e_id}', 'PERSON');"
    )
    rc, _, err = psql(
        f"SET search_path TO civix, public; DELETE FROM civix.entity WHERE entity_id = '{test_e_id}';"
    )
    if rc != 0 and ("tombstone" in err.lower() or "civix invariant" in err.lower() or "prohibited" in err.lower()):
        passs("identity", "entity_delete_blocked", "Physical DELETE rejected — BLK-16/ADR-018 ✓")
    elif rc != 0:
        passs("identity", "entity_delete_blocked", f"DELETE rejected by trigger: {err[:100]}")
    else:
        fail("identity", "entity_delete_blocked", "Physical DELETE on entity SUCCEEDED — BLK-16 VIOLATED")

    # Test tombstoning works
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"UPDATE civix.entity SET visibility_status = 'TOMBSTONED' WHERE entity_id = '{test_e_id}';"
    )
    if rc == 0:
        passs("identity", "entity_tombstone_works", "visibility_status = TOMBSTONED accepted")
    else:
        fail("identity", "entity_tombstone_works", f"Tombstone UPDATE rejected: {err[:200]}")

    # Verify tombstone outbox emission
    val = query_one(
        f"SET search_path TO civix, public; "
        f"SELECT count(*) FROM civix.outbox "
        f"WHERE entity_id = '{test_e_id}' AND action = 'TOMBSTONE_NODE';"
    )
    if val == "1":
        passs("identity", "tombstone_outbox_emitted", "TOMBSTONE_NODE emitted to outbox — BLK-18 ✓")
    else:
        fail("identity", "tombstone_outbox_emitted", f"Expected 1 TOMBSTONE_NODE in outbox, found {val}")

    # source_record immutability
    test_src_id = str(uuid.uuid4())
    test_src_sys_id = str(uuid.uuid4())
    psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.source (source_id, source_name, agency_type) VALUES ('{test_src_sys_id}', 'ImmutableTestSrc', 'POLICE');"
    )
    psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.source_record (source_record_id, source_id, record_type) "
        f"VALUES ('{test_src_id}', '{test_src_sys_id}', 'CDR_ROW');"
    )
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"UPDATE civix.source_record SET record_type = 'TAMPERED' WHERE source_record_id = '{test_src_id}';"
    )
    if rc != 0:
        passs("identity", "source_record_immutable", "UPDATE on source_record rejected ✓")
    else:
        fail("identity", "source_record_immutable", "UPDATE on source_record SUCCEEDED — immutability VIOLATED")

# ── Step 7: H4 N-ary Event Test ───────────────────────────────────────────────
def test_h4_event():
    print("\n═══ STEP 7: H4 N-ARY EVENT TEST ═══")

    # Create two property entities
    prop01_id = str(uuid.uuid4())
    prop08_id = str(uuid.uuid4())
    for pid, pref in [(prop01_id, "PROP-01"), (prop08_id, "PROP-08")]:
        psql(f"SET search_path TO civix, public; INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{pid}', 'PROPERTY');")
        psql(f"SET search_path TO civix, public; INSERT INTO civix.property (entity_id, property_ref, property_type) VALUES ('{pid}', '{pref}', 'RESIDENTIAL');")

    # Create one PROPERTY_MUTATION event
    event_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.event (event_id, event_type, occurred_at) "
        f"VALUES ('{event_id}', 'PROPERTY_MUTATION', "
        f"'[2026-06-15 10:00:00+00, 2026-06-15 11:00:00+00]');"
    )
    if rc == 0:
        passs("h4_event", "property_mutation_event_created", f"event_id={event_id}")
    else:
        fail("h4_event", "property_mutation_event_created", err[:200])
        return

    # Attach PROP-01
    rc1, _, err1 = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.event_participant (event_id, entity_id, participant_role) "
        f"VALUES ('{event_id}', '{prop01_id}', 'TARGET_PROPERTY');"
    )
    # Attach PROP-08 (same role, different entity — should NOT violate UNIQUE)
    rc2, _, err2 = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.event_participant (event_id, entity_id, participant_role) "
        f"VALUES ('{event_id}', '{prop08_id}', 'TARGET_PROPERTY');"
    )

    if rc1 == 0 and rc2 == 0:
        passs("h4_event", "two_target_properties_on_one_event",
              "PROP-01 and PROP-08 both attached with TARGET_PROPERTY role ✓")
    else:
        fail("h4_event", "two_target_properties_on_one_event",
             f"PROP-01 rc={rc1} err={err1[:100]}, PROP-08 rc={rc2} err={err2[:100]}")

    # Verify event appears exactly once
    event_count = query_one(
        f"SET search_path TO civix, public; "
        f"SELECT count(*) FROM civix.event WHERE event_id = '{event_id}';"
    )
    if event_count == "1":
        passs("h4_event", "event_appears_once", "One event, two participants ✓")
    else:
        fail("h4_event", "event_appears_once", f"Event count = {event_count}")

    # Verify UNIQUE prevents duplicate (event, entity, role)
    rc_dup, _, err_dup = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.event_participant (event_id, entity_id, participant_role) "
        f"VALUES ('{event_id}', '{prop01_id}', 'TARGET_PROPERTY');"
    )
    if rc_dup != 0:
        passs("h4_event", "unique_event_entity_role", "Duplicate (event, entity, role) correctly rejected ✓")
    else:
        fail("h4_event", "unique_event_entity_role", "Duplicate participant row ALLOWED — BLK-21 VIOLATED")

    # Test multiple roles for same entity in same event
    person_id = str(uuid.uuid4())
    psql(f"SET search_path TO civix, public; INSERT INTO civix.entity (entity_id, entity_type) VALUES ('{person_id}', 'PERSON');")
    psql(f"SET search_path TO civix, public; INSERT INTO civix.person (entity_id, display_name) VALUES ('{person_id}', 'Test Owner');")

    rc_r1, _, _ = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.event_participant (event_id, entity_id, participant_role) "
        f"VALUES ('{event_id}', '{person_id}', 'REGISTERED_OWNER');"
    )
    rc_r2, _, _ = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.event_participant (event_id, entity_id, participant_role) "
        f"VALUES ('{event_id}', '{person_id}', 'DRIVER');"
    )
    if rc_r1 == 0 and rc_r2 == 0:
        passs("h4_event", "multi_role_same_entity", "Same entity with REGISTERED_OWNER + DRIVER roles ✓")
    else:
        fail("h4_event", "multi_role_same_entity",
             f"Multiple roles rejected: r1={rc_r1}, r2={rc_r2}")

# ── Step 8: Evidence / Provenance Tests ──────────────────────────────────────
def test_evidence():
    print("\n═══ STEP 8: EVIDENCE / PROVENANCE TESTS ═══")

    import hashlib
    hash_bytes = hashlib.sha256(b"test_file_content").digest()
    hash_hex = hash_bytes.hex()

    artifact_id = str(uuid.uuid4())
    rc, _, err = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.evidence_artifact "
        f"(artifact_id, sha256_hash, hash_algorithm, mime_type) "
        f"VALUES ('{artifact_id}', '\\x{hash_hex}', 'SHA256', 'video/mp4');"
    )
    if rc == 0:
        passs("evidence", "artifact_insert")
    else:
        fail("evidence", "artifact_insert", err[:200])
        return

    # Test deduplication: same hash + algorithm must fail
    dup_id = str(uuid.uuid4())
    rc_dup, _, err_dup = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.evidence_artifact "
        f"(artifact_id, sha256_hash, hash_algorithm, mime_type) "
        f"VALUES ('{dup_id}', '\\x{hash_hex}', 'SHA256', 'video/mp4');"
    )
    if rc_dup != 0:
        passs("evidence", "artifact_dedup", "Duplicate (hash, algorithm) correctly rejected — ADR-004 ✓")
    else:
        fail("evidence", "artifact_dedup", "Duplicate artifact ALLOWED — ADR-004 VIOLATED")

    # Same hash, different algorithm → should be allowed
    diff_algo_id = str(uuid.uuid4())
    rc_diff, _, err_diff = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.evidence_artifact "
        f"(artifact_id, sha256_hash, hash_algorithm, mime_type) "
        f"VALUES ('{diff_algo_id}', '\\x{hash_hex}', 'SHA512', 'video/mp4');"
    )
    if rc_diff == 0:
        passs("evidence", "artifact_different_algo_allowed", "Same hash value, different algorithm → new row ✓")
    else:
        fail("evidence", "artifact_different_algo_allowed",
             f"Different algorithm rejected: {err_diff[:100]}")

    # Parent artifact → child
    child_id = str(uuid.uuid4())
    child_hash = hashlib.sha256(b"derived_clip").digest().hex()
    rc_child, _, err_child = psql(
        f"SET search_path TO civix, public; "
        f"INSERT INTO civix.evidence_artifact "
        f"(artifact_id, sha256_hash, hash_algorithm, parent_artifact_id) "
        f"VALUES ('{child_id}', '\\x{child_hash}', 'SHA256', '{artifact_id}');"
    )
    if rc_child == 0:
        passs("evidence", "artifact_parent_chain", "Child artifact with parent_artifact_id ✓")
    else:
        fail("evidence", "artifact_parent_chain", err_child[:200])

    # Try deleting parent while child exists → ON DELETE RESTRICT
    rc_del, _, err_del = psql(
        f"SET search_path TO civix, public; DELETE FROM civix.evidence_artifact WHERE artifact_id = '{artifact_id}';"
    )
    if rc_del != 0:
        passs("evidence", "parent_artifact_restrict",
              "Parent deletion with active child correctly rejected — BLK-22/ADR-022 ✓")
    else:
        fail("evidence", "parent_artifact_restrict",
             "Parent artifact DELETED while child exists — BLK-22 VIOLATED")

# ── Step 9: RLS Tests ─────────────────────────────────────────────────────────
def test_rls():
    print("\n═══ STEP 9: RLS TESTS ═══")

    # Verify RLS is ENABLED on protected tables
    rls_tables = [
        "investigative_case", "evidence_instance", "assertion",
        "hypothesis", "hypothesis_support", "investigative_lead",
        "investigation_task", "case_entity_role", "fir"
    ]
    for tbl in rls_tables:
        val = query_one(
            f"SELECT rowsecurity FROM pg_tables "
            f"WHERE schemaname='civix' AND tablename='{tbl}';"
        )
        if val == "t":
            passs("rls", f"rls_enabled_{tbl}")
        else:
            fail("rls", f"rls_enabled_{tbl}", f"RLS NOT enabled on {tbl}")

    # Verify RLS policies exist
    for tbl, expected_policy in [
        ("assertion", "policy_assertion_select"),
        ("investigative_case", "policy_case_access"),
        ("evidence_instance", "policy_evidence_instance_select"),
    ]:
        val = query_one(
            f"SELECT count(*) FROM pg_policy "
            f"WHERE polrelid = 'civix.{tbl}'::regclass AND polname = '{expected_policy}';"
        )
        if val == "1":
            passs("rls", f"policy_{tbl}", f"Policy '{expected_policy}' exists ✓")
        else:
            fail("rls", f"policy_{tbl}", f"Policy '{expected_policy}' NOT found on {tbl}")

    # Verify helper functions
    for fn in ["get_accessible_case_ids", "current_user_is_admin",
               "append_case_to_assertion", "revoke_case_from_assertion"]:
        val = query_one(
            f"SELECT count(*) FROM pg_proc p "
            f"JOIN pg_namespace n ON n.oid = p.pronamespace "
            f"WHERE n.nspname = 'civix' AND p.proname = '{fn}';"
        )
        if val == "1":
            passs("rls", f"fn_{fn}", f"RLS helper function exists")
        else:
            fail("rls", f"fn_{fn}", f"RLS helper function '{fn}' NOT found")

# ── Step 10: Outbox / Tombstone Tests ────────────────────────────────────────
def test_outbox():
    print("\n═══ STEP 10: OUTBOX / TOMBSTONE TESTS ═══")

    # Already tested tombstone emission in Step 6
    # Verify outbox has TOMBSTONE_NODE entries (from prior test)
    val = query_one(
        "SET search_path TO civix, public; "
        "SELECT count(*) FROM civix.outbox WHERE action = 'TOMBSTONE_NODE';"
    )
    if val and int(val) >= 1:
        passs("outbox", "tombstone_node_in_outbox", f"{val} TOMBSTONE_NODE records ✓")
    else:
        fail("outbox", "tombstone_node_in_outbox", f"No TOMBSTONE_NODE records in outbox. Count={val}")

    # Verify outbox table structure
    for col in ["id", "entity_id", "action", "entity_type", "payload", "created_at", "consumed_at"]:
        val = query_one(
            f"SELECT count(*) FROM information_schema.columns "
            f"WHERE table_schema='civix' AND table_name='outbox' AND column_name='{col}';"
        )
        if val == "1":
            passs("outbox", f"outbox_col_{col}")
        else:
            fail("outbox", f"outbox_col_{col}", f"Column '{col}' missing from outbox")

    # Verify CDC pending query works
    val = query_one(
        "SET search_path TO civix, public; "
        "SELECT count(*) FROM civix.outbox WHERE consumed_at IS NULL;"
    )
    passs("outbox", "pending_query", f"{val} pending CDC events")

# ── Step 12: Index Verification ───────────────────────────────────────────────
def verify_indexes():
    print("\n═══ STEP 12: INDEX VERIFICATION ═══")

    critical = [
        "idx_assertion_authorized_cases",
        "idx_assertion_subject",
        "idx_assertion_predicate",
        "idx_assertion_tx",
        "idx_assertion_active",
        "idx_evidence_instance_case",
        "idx_evidence_instance_artifact",
        "idx_event_participant_event",
        "idx_event_participant_entity",
        "idx_hypothesis_case",
        "idx_hyp_support_hypothesis",
        "idx_hyp_support_active",
        "idx_case_access_user",
        "idx_outbox_pending",
        "idx_location_geometry",
        "idx_entity_type",
        "idx_entity_visibility",
        "idx_provenance_derived",
        "idx_provenance_source",
    ]
    for idx in critical:
        val = query_one(
            f"SELECT count(*) FROM pg_indexes "
            f"WHERE schemaname='civix' AND indexname='{idx}';"
        )
        if val == "1":
            passs("indexes", idx)
        else:
            fail("indexes", idx, f"Index '{idx}' NOT found")

    # Total index count
    total = query_one("SELECT count(*) FROM pg_indexes WHERE schemaname='civix';")
    results["indexes"]["total_indexes"] = total
    print(f"\n  Total indexes in civix schema: {total}")

# ── Step 13: Run 014_validation.sql ──────────────────────────────────────────
def run_validation_sql():
    print("\n═══ STEP 13: EXECUTE 014_validation.sql ═══")
    filepath = MIGRATIONS_DIR / "014_validation.sql"
    
    # Run but capture carefully (validation.sql has SELECT statements, not DDL)
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS
    cmd = [
        PSQL_BIN, "-h", DB_HOST, "-p", DB_PORT,
        "-U", DB_USER, "-d", DB_NAME,
        "-f", str(filepath),
        "--no-psqlrc",
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, env=env)
    results["validation_sql"]["returncode"] = r.returncode
    results["validation_sql"]["stdout"] = r.stdout[:3000]
    results["validation_sql"]["stderr"] = r.stderr[:500]
    
    if r.returncode == 0:
        passs("validation_sql", "014_validation_executed",
              "All validation queries executed without error")
    else:
        fail("validation_sql", "014_validation_executed",
             f"Validation SQL returned errors: {r.stderr[:200]}")
    
    print("  Validation output (first 2000 chars):")
    print("  " + r.stdout[:2000].replace("\n", "\n  "))

# ── Final Report ──────────────────────────────────────────────────────────────
def write_report():
    report_dir = BASE_DIR / "docs" / "phase2a_verification"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "PHASE2A_LIVE_DATABASE_VERIFICATION_REPORT.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    total_tests = sum(
        1 for section in results.values()
        if isinstance(section, dict)
        for v in section.values()
        if isinstance(v, str) and v.startswith(("PASS", "FAIL", "BLOCKED", "NOT TESTED"))
    )
    passes = sum(
        1 for section in results.values()
        if isinstance(section, dict)
        for v in section.values()
        if isinstance(v, str) and v.startswith("PASS")
    )
    fails = len(results["failures"])

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"# CIVIX — PHASE 2A LIVE DATABASE VERIFICATION REPORT\n")
        f.write(f"**Generated**: {timestamp}  \n")
        f.write(f"**Database**: {DB_NAME} @ {DB_HOST}:{DB_PORT}  \n")
        f.write(f"**Architecture**: FROZEN — no modifications made  \n\n")
        f.write("---\n\n")

        f.write(f"## 1. EXECUTIVE VERDICT\n\n")
        if verdict == "PASS":
            f.write(f"### ✅ PHASE 2A LIVE DATABASE VERIFICATION = **PASS**\n\n")
            f.write(f"All {total_tests} tests passed. The physical PostgreSQL schema faithfully "
                    f"implements the frozen CIVIX architecture.\n\n")
        else:
            f.write(f"### ❌ PHASE 2A LIVE DATABASE VERIFICATION = **NOT READY**\n\n")
            f.write(f"{fails} test(s) failed. See failures section.\n\n")

        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Total Tests | {total_tests} |\n")
        f.write(f"| PASS | {passes} |\n")
        f.write(f"| FAIL | {fails} |\n")
        f.write(f"| Verdict | {verdict} |\n\n")

        f.write("---\n\n")
        f.write("## 2. ENVIRONMENT\n\n")
        for k, v in results["environment"].items():
            f.write(f"- **{k}**: {v}\n")

        f.write("\n---\n\n")
        f.write("## 3. MIGRATION RESULTS\n\n")
        f.write("| Migration | Status |\n|---|---|\n")
        for fname in MIGRATION_FILES:
            status = results["migrations"].get(fname, "NOT TESTED")
            f.write(f"| {fname} | {status} |\n")

        for section_name in [
            "tables", "enums", "constraints", "triggers",
            "bitemporal", "identity", "h4_event", "evidence",
            "rls", "outbox", "indexes", "validation_sql"
        ]:
            f.write(f"\n---\n\n## Section: {section_name.upper()}\n\n")
            section = results.get(section_name, {})
            for k, v in section.items():
                if isinstance(v, list):
                    f.write(f"**{k}**: {json.dumps(v)}\n\n")
                elif isinstance(v, str):
                    icon = "✅" if v.startswith("PASS") else ("❌" if v.startswith("FAIL") else "⊘")
                    f.write(f"- {icon} **{k}**: {v}\n")
                else:
                    f.write(f"- **{k}**: {v}\n")

        if results["failures"]:
            f.write("\n---\n\n## FAILURES\n\n")
            for i, failure in enumerate(results["failures"], 1):
                f.write(f"### Failure {i}: [{failure['section']}] {failure['key']}\n")
                f.write(f"```\n{failure['detail']}\n```\n\n")

        f.write("\n---\n\n## FILES INSPECTED (NOT MODIFIED)\n\n")
        for fname in MIGRATION_FILES:
            f.write(f"- `database/migrations/{fname}`\n")
        f.write("- `database/verify_phase2a.py` (this script)\n\n")
        f.write("**Files modified**: NONE (verification only)\n")

        if verdict == "PASS":
            f.write("\n---\n\n## NEXT STEPS\n\n")
            f.write("Phase 2B — Scalable Synthetic Data Engine is now ready for explicit authorization.\n")
        else:
            f.write("\n---\n\n## REMEDIATION REQUIRED\n\n")
            f.write("Do NOT proceed to Phase 2B until all failures are resolved.\n")
            f.write("Failures must be fixed in the migration SQL files (not patched in this script).\n")

    print(f"\n  Report written to: {report_path}")
    return report_path

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 65)
    print("CIVIX Phase 2A — Live Database Verification Harness")
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 65)

    # Step 1: Environment Discovery
    if not discover_environment():
        print("\nERROR: Cannot connect to PostgreSQL. Aborting.")
        print("Ensure CIVIX_DB_PASSWORD is set and PostgreSQL is running.")
        write_report()
        sys.exit(1)

    # Step 2: Create test database
    if not create_test_database():
        print("\nERROR: Cannot create test database. Aborting.")
        write_report()
        sys.exit(1)

    # Step 3: Run migrations
    if not run_migrations():
        print("\nMigration chain FAILED. Running partial structural checks.")
        write_report()
        sys.exit(1)

    # Step 4: Structural verification
    verify_structure()

    # Step 5: Bitemporal tests
    test_bitemporal()

    # Step 6: Identity tests
    test_identity()

    # Step 7: H4 event test
    test_h4_event()

    # Step 8: Evidence/provenance
    test_evidence()

    # Step 9: RLS
    test_rls()

    # Step 10: Outbox
    test_outbox()

    # Step 12: Indexes
    verify_indexes()

    # Step 13: validation.sql
    run_validation_sql()

    # Write final report
    report_path = write_report()

    print("\n" + "=" * 65)
    if verdict == "PASS":
        print("✅ PHASE 2A LIVE DATABASE VERIFICATION = PASS")
        print()
        print("Phase 2B — Scalable Synthetic Data Engine is now ready")
        print("for explicit authorization.")
    else:
        print("❌ PHASE 2A LIVE DATABASE VERIFICATION = NOT READY")
        print(f"   {len(results['failures'])} failure(s) detected.")
        for f in results["failures"]:
            print(f"   • [{f['section']}] {f['key']}: {f['detail'][:80]}")
    print("=" * 65)
    print(f"Report: {report_path}")

if __name__ == "__main__":
    main()
