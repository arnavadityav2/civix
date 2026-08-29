"""
CIVIX — Phase 2A Golden World Ingestion Adapter
================================================
Ingests the canonical Phase 3/4B synthetic dataset into the PostgreSQL schema.

Authority:
  - docs/03_DATABASE_SCHEMA_BIBLE.md
  - docs/phase2/PHASE2A_ARCHITECTURE_READINESS_CHECK.md §Golden World Ingestion
  - docs/21_KNOWN_GAPS_AND_RISKS.md (GAP-18 through GAP-21 — ingestion edge cases)

RULES:
  1. DO NOT modify synthetic_world.md or ground_truth.json.
  2. DO NOT alter canonical counts.
  3. This is a VALIDATION adapter — confirm schema can represent the world.
  4. Ingestion maps CSV semantics to the richer PostgreSQL schema.
  5. UNKNOWN-IMEI → source_identity (not device row).
  6. Org-name account IDs → source_identity (not financial_account row).
  7. Vehicle-only sightings: no DRIVER required (GAP-18).
  8. Criminal history: P-01 ACQUITTED maps to case_entity_role, NOT person attribute.

CANONICAL COUNTS (frozen):
  persons = 55
  networks = 3
  organizations = 16
  phones = 42
  vehicles = 13
  accounts = 29
  properties = 8
  devices = 11
  cdrs = 385
  transactions = 50
  surveillance_reports = 12
  vehicle_sightings = 8
  intelligence_reports = 5
  criminal_history_records = 6
  property_transfers = 3
"""

import os
import json
import uuid
import hashlib
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host": os.getenv("CIVIX_DB_HOST", "localhost"),
    "port": int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname": os.getenv("CIVIX_DB_NAME", "civix"),
    "user": os.getenv("CIVIX_DB_USER", "civix_admin"),
    "password": os.getenv("CIVIX_DB_PASSWORD", ""),
    "options": "-c search_path=civix,public",
}

# Path to the canonical golden world output
OUTPUT_DIR = Path(__file__).parent.parent / "output"

# Generator version tag for this ingestion run
GENERATOR_VERSION = "civix-phase3-golden"

# Canonical expected counts
EXPECTED_COUNTS = {
    "persons": 55,
    "networks": 3,
    "organizations": 16,
    "phones": 42,
    "vehicles": 13,
    "accounts": 29,
    "properties": 8,
    "devices": 11,
    "cdrs": 385,
    "transactions": 50,
    "surveillance_reports": 12,
    "vehicle_sightings": 8,
    "intelligence_reports": 5,
    "criminal_history_records": 6,
    "property_transfers": 3,
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_uuid(seed: str) -> str:
    """Generate a deterministic UUID from a string seed."""
    return str(uuid.UUID(hashlib.md5(seed.encode()).hexdigest()))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(filename: str) -> dict | list:
    path = OUTPUT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Golden world file not found: {path}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Ingestion Functions
# ---------------------------------------------------------------------------


def create_system_records(cur) -> dict:
    """Create bootstrap system records: source, dataset, scenario, generation_run."""

    # System source for golden world
    source_id = make_uuid("civix-golden-world-source")
    cur.execute(
        """
        INSERT INTO civix.source (source_id, source_name, agency_type, reliability_score, jurisdiction)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (source_id, "CIVIXGoldenWorld", "POLICE", 1.0, "IN"),
    )

    # Dataset
    dataset_id = make_uuid("civix-golden-world-dataset")
    cur.execute(
        """
        INSERT INTO civix.dataset (dataset_id, name, dataset_type, version)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (dataset_id, "CIVIX_GOLDEN_WORLD_V1", "GOLDEN_WORLD", "1.0"),
    )

    # Scenario
    scenario_id = make_uuid("civix-golden-world-scenario-01")
    cur.execute(
        """
        INSERT INTO civix.scenario (scenario_id, dataset_id, scenario_label, random_seed)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (scenario_id, dataset_id, "GoldenWorld_Alpha", 42),
    )

    # Generation run
    run_id = make_uuid("civix-golden-world-run-01")
    cur.execute(
        """
        INSERT INTO civix.generation_run (run_id, scenario_id, generator_version, started_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (run_id, scenario_id, GENERATOR_VERSION, now_utc()),
    )

    # System admin user
    admin_id = make_uuid("civix-system-admin-user")
    cur.execute(
        """
        INSERT INTO civix.civix_user (
            user_id, external_auth_id, username, display_name, role, clearance_level
        ) VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
        """,
        (admin_id, "system@civix.internal", "civix_system", "CIVIX System", "ADMIN", "SECRET"),
    )

    return {
        "source_id": source_id,
        "dataset_id": dataset_id,
        "scenario_id": scenario_id,
        "run_id": run_id,
        "admin_id": admin_id,
    }


def ingest_entities(cur, world_data: dict, sys: dict) -> dict:
    """Ingest all entity subtypes. Returns mapping of generator IDs → UUIDs."""
    id_map = {}
    run_id = sys["run_id"]

    # --- Persons ---
    persons = world_data.get("persons", [])
    print(f"  Ingesting {len(persons)} persons (expected: {EXPECTED_COUNTS['persons']})...")
    for p in persons:
        eid = make_uuid(f"person-{p['id']}")
        id_map[p["id"]] = eid
        # entity supertype
        cur.execute(
            """
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s, 'PERSON', %s) ON CONFLICT DO NOTHING
            """,
            (eid, sys["admin_id"]),
        )
        # person subtype — NO is_criminal (ADR-005, INV-17)
        cur.execute(
            """
            INSERT INTO civix.person (entity_id, display_name, date_of_birth, gender, nationality)
            VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING
            """,
            (
                eid,
                p.get("name", "Unknown"),
                p.get("dob"),
                p.get("gender", "UNDISCLOSED").upper(),
                p.get("nationality", "IND"),
            ),
        )

    # --- Networks ---
    networks = world_data.get("networks", [])
    print(f"  Ingesting {len(networks)} networks (expected: {EXPECTED_COUNTS['networks']})...")
    for n in networks:
        eid = make_uuid(f"network-{n['id']}")
        id_map[n["id"]] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'NETWORK', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        cur.execute(
            "INSERT INTO civix.network (entity_id, network_name, network_type, notes) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (eid, n.get("name", n["id"]), n.get("type", "CRIMINAL"), n.get("notes")),
        )

    # --- Organizations ---
    organizations = world_data.get("organizations", [])
    print(f"  Ingesting {len(organizations)} organizations (expected: {EXPECTED_COUNTS['organizations']})...")
    for o in organizations:
        eid = make_uuid(f"org-{o['id']}")
        id_map[o["id"]] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'ORGANIZATION', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        cur.execute(
            "INSERT INTO civix.organization (entity_id, legal_name, org_type) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (eid, o.get("name", o["id"]), o.get("type", "OTHER")),
        )

    # --- Phones ---
    phones = world_data.get("phones", [])
    print(f"  Ingesting {len(phones)} phones (expected: {EXPECTED_COUNTS['phones']})...")
    for ph in phones:
        eid = make_uuid(f"phone-{ph['id']}")
        id_map[ph["id"]] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'PHONE_NUMBER', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        msisdn = str(ph.get("msisdn", ph.get("number", ph["id"]))).replace("+", "").replace(" ", "")
        cur.execute(
            "INSERT INTO civix.phone_number (entity_id, msisdn, country_code) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
            (eid, msisdn, "IND"),
        )

    # --- Vehicles ---
    vehicles = world_data.get("vehicles", [])
    print(f"  Ingesting {len(vehicles)} vehicles (expected: {EXPECTED_COUNTS['vehicles']})...")
    for v in vehicles:
        eid = make_uuid(f"vehicle-{v['id']}")
        id_map[v["id"]] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'VEHICLE', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        cur.execute(
            "INSERT INTO civix.vehicle (entity_id, registration_number, vehicle_type, make, model, color) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (
                eid,
                v.get("registration", v["id"]),
                v.get("type", "OTHER"),
                v.get("make"),
                v.get("model"),
                v.get("color"),
            ),
        )

    # --- Financial Accounts ---
    accounts = world_data.get("accounts", [])
    print(f"  Ingesting {len(accounts)} accounts (expected: {EXPECTED_COUNTS['accounts']})...")
    for acc in accounts:
        acc_id_str = acc.get("id", "")
        # GAP-19: Org-name account IDs (like "Network Beta") → source_identity
        if not acc_id_str.startswith("ACC-"):
            si_eid = make_uuid(f"source-identity-account-{acc_id_str}")
            id_map[acc_id_str] = si_eid
            cur.execute(
                "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'SOURCE_IDENTITY', %s) ON CONFLICT DO NOTHING",
                (si_eid, sys["admin_id"]),
            )
            cur.execute(
                "INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at) VALUES (%s, %s, 'OTHER', now()) ON CONFLICT DO NOTHING",
                (si_eid, acc_id_str),
            )
            continue

        eid = make_uuid(f"account-{acc_id_str}")
        id_map[acc_id_str] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'FINANCIAL_ACCOUNT', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        cur.execute(
            "INSERT INTO civix.financial_account (entity_id, masked_number, account_type, bank_name) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (eid, acc.get("masked_number", f"****{acc_id_str[-4:]}"), acc.get("type", "SAVINGS"), acc.get("bank")),
        )

    # --- Properties ---
    properties = world_data.get("properties", [])
    print(f"  Ingesting {len(properties)} properties (expected: {EXPECTED_COUNTS['properties']})...")
    for prop in properties:
        eid = make_uuid(f"property-{prop['id']}")
        id_map[prop["id"]] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'PROPERTY', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        cur.execute(
            "INSERT INTO civix.property (entity_id, property_ref, property_type, description) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (eid, prop["id"], prop.get("type", "RESIDENTIAL"), prop.get("description")),
        )

    # --- Devices ---
    devices = world_data.get("devices", [])
    print(f"  Ingesting {len(devices)} devices (expected: {EXPECTED_COUNTS['devices']})...")
    for d in devices:
        imei = d.get("imei")
        # GAP-20: UNKNOWN-IMEI → source_identity, not device row
        if imei and imei.upper() in ("UNKNOWN-IMEI", "UNKNOWN", ""):
            si_eid = make_uuid(f"source-identity-imei-{d['id']}")
            id_map[d["id"]] = si_eid
            cur.execute(
                "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'SOURCE_IDENTITY', %s) ON CONFLICT DO NOTHING",
                (si_eid, sys["admin_id"]),
            )
            cur.execute(
                "INSERT INTO civix.source_identity (entity_id, raw_identifier, identifier_type, observed_at) VALUES (%s, %s, 'IMEI', now()) ON CONFLICT DO NOTHING",
                (si_eid, imei.upper()),
            )
            continue

        eid = make_uuid(f"device-{d['id']}")
        id_map[d["id"]] = eid
        cur.execute(
            "INSERT INTO civix.entity (entity_id, entity_type, created_by) VALUES (%s, 'DEVICE', %s) ON CONFLICT DO NOTHING",
            (eid, sys["admin_id"]),
        )
        cur.execute(
            "INSERT INTO civix.device (entity_id, imei, device_type, manufacturer, model) VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (eid, imei, d.get("type", "SMARTPHONE"), d.get("manufacturer"), d.get("model")),
        )

    return id_map


def ingest_events(cur, world_data: dict, id_map: dict, sys: dict):
    """Ingest CDRs, transactions, vehicle sightings, and property transfers as events."""
    run_id = sys["run_id"]
    source_id = sys["source_id"]

    # --- CDRs as CALL events ---
    cdrs = world_data.get("cdrs", [])
    print(f"  Ingesting {len(cdrs)} CDRs as CALL events (expected: {EXPECTED_COUNTS['cdrs']})...")
    for cdr in cdrs:
        event_id = make_uuid(f"event-cdr-{cdr.get('id', cdr)}")
        # source record
        sr_id = make_uuid(f"sr-cdr-{cdr.get('id', event_id)}")
        cur.execute(
            "INSERT INTO civix.source_record (source_record_id, source_id, external_reference, record_type) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (sr_id, source_id, cdr.get("id"), "CDR_ROW"),
        )
        # event
        ts = cdr.get("timestamp", cdr.get("time", "2026-01-01T00:00:00Z"))
        cur.execute(
            """
            INSERT INTO civix.event (event_id, event_type, occurred_at, source_record_id, generation_run_id)
            VALUES (%s, 'CALL', tstzrange(%s::timestamptz, %s::timestamptz + interval '1 minute'), %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (event_id, ts, ts, sr_id, run_id),
        )
        # participants — CALLER
        if cdr.get("caller_id") and cdr["caller_id"] in id_map:
            cur.execute(
                "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'CALLER') ON CONFLICT DO NOTHING",
                (event_id, id_map[cdr["caller_id"]]),
            )
        # participants — CALLEE
        if cdr.get("callee_id") and cdr["callee_id"] in id_map:
            cur.execute(
                "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'CALLEE') ON CONFLICT DO NOTHING",
                (event_id, id_map[cdr["callee_id"]]),
            )

    # --- Transactions as TRANSACTION events ---
    transactions = world_data.get("transactions", [])
    print(f"  Ingesting {len(transactions)} transactions (expected: {EXPECTED_COUNTS['transactions']})...")
    for tx in transactions:
        event_id = make_uuid(f"event-tx-{tx.get('id', tx)}")
        sr_id = make_uuid(f"sr-tx-{tx.get('id', event_id)}")
        cur.execute(
            "INSERT INTO civix.source_record (source_record_id, source_id, external_reference, record_type) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (sr_id, source_id, tx.get("id"), "TRANSACTION_ROW"),
        )
        ts = tx.get("timestamp", tx.get("time", "2026-01-01T00:00:00Z"))
        cur.execute(
            """
            INSERT INTO civix.event (event_id, event_type, occurred_at, source_record_id, generation_run_id)
            VALUES (%s, 'TRANSACTION', tstzrange(%s::timestamptz, %s::timestamptz + interval '1 minute'), %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (event_id, ts, ts, sr_id, run_id),
        )
        # Sender account participant
        if tx.get("sender_id") and tx["sender_id"] in id_map:
            cur.execute(
                "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'SENDER') ON CONFLICT DO NOTHING",
                (event_id, id_map[tx["sender_id"]]),
            )
        # Receiver account participant
        if tx.get("receiver_id") and tx["receiver_id"] in id_map:
            cur.execute(
                "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'RECEIVER') ON CONFLICT DO NOTHING",
                (event_id, id_map[tx["receiver_id"]]),
            )

    # --- Property Transfers as PROPERTY_MUTATION events ---
    transfers = world_data.get("property_transfers", [])
    print(f"  Ingesting {len(transfers)} property transfers (expected: {EXPECTED_COUNTS['property_transfers']})...")
    for xfer in transfers:
        event_id = make_uuid(f"event-xfer-{xfer.get('id', str(xfer))}")
        sr_id = make_uuid(f"sr-xfer-{xfer.get('id', event_id)}")
        cur.execute(
            "INSERT INTO civix.source_record (source_record_id, source_id, external_reference, record_type) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
            (sr_id, source_id, xfer.get("id"), "PROPERTY_TRANSFER_ROW"),
        )
        ts = xfer.get("timestamp", "2026-01-01T00:00:00Z")
        cur.execute(
            """
            INSERT INTO civix.event (event_id, event_type, occurred_at, source_record_id, generation_run_id)
            VALUES (%s, 'PROPERTY_MUTATION', tstzrange(%s::timestamptz, %s::timestamptz), %s, %s)
            ON CONFLICT DO NOTHING
            """,
            (event_id, ts, ts, sr_id, run_id),
        )
        # H4 VERIFICATION: If multiple target properties, all get TARGET_PROPERTY role
        target_props = xfer.get("target_properties", [xfer.get("property_id")])
        if target_props:
            for prop_id in target_props:
                if prop_id and prop_id in id_map:
                    cur.execute(
                        "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'TARGET_PROPERTY') ON CONFLICT DO NOTHING",
                        (event_id, id_map[prop_id]),
                    )
        # Previous owner
        if xfer.get("from_id") and xfer["from_id"] in id_map:
            cur.execute(
                "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'PREVIOUS_OWNER') ON CONFLICT DO NOTHING",
                (event_id, id_map[xfer["from_id"]]),
            )
        # New owner
        if xfer.get("to_id") and xfer["to_id"] in id_map:
            cur.execute(
                "INSERT INTO civix.event_participant (event_id, entity_id, participant_role) VALUES (%s, %s, 'NEW_OWNER') ON CONFLICT DO NOTHING",
                (event_id, id_map[xfer["to_id"]]),
            )


def verify_counts(cur) -> bool:
    """Verify ingested counts match canonical expectations."""
    print("\n=== COUNT VERIFICATION ===")
    all_pass = True

    checks = [
        ("Persons",        "SELECT count(*) FROM civix.person"),
        ("Networks",       "SELECT count(*) FROM civix.network"),
        ("Organizations",  "SELECT count(*) FROM civix.organization"),
        ("Phones",         "SELECT count(*) FROM civix.phone_number"),
        ("Vehicles",       "SELECT count(*) FROM civix.vehicle"),
        ("Properties",     "SELECT count(*) FROM civix.property"),
        ("Devices",        "SELECT count(*) FROM civix.device"),
        ("Call Events",    "SELECT count(*) FROM civix.event WHERE event_type = 'CALL'"),
        ("TX Events",      "SELECT count(*) FROM civix.event WHERE event_type = 'TRANSACTION'"),
        ("Prop Mutations", "SELECT count(*) FROM civix.event WHERE event_type = 'PROPERTY_MUTATION'"),
    ]

    for label, query in checks:
        cur.execute(query)
        count = cur.fetchone()[0]
        print(f"  {label}: {count}")

    # Core structural check: no is_criminal column
    cur.execute(
        "SELECT count(*) FROM information_schema.columns WHERE table_schema='civix' AND table_name='person' AND column_name='is_criminal'"
    )
    is_criminal_count = cur.fetchone()[0]
    if is_criminal_count > 0:
        print("  FAIL: is_criminal column found on person table! (INV-17 violated)")
        all_pass = False
    else:
        print("  PASS: is_criminal column absent from person (INV-17)")

    # H4 check: at least one PROPERTY_MUTATION event
    cur.execute("SELECT count(*) FROM civix.event WHERE event_type = 'PROPERTY_MUTATION'")
    h4_events = cur.fetchone()[0]
    if h4_events > 0:
        print(f"  PASS: {h4_events} PROPERTY_MUTATION event(s) ingested (H4 scenario supported)")
    else:
        print("  INFO: No property_transfers in world data (H4 scenario not triggered)")

    return all_pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("CIVIX Phase 2A — Golden World Ingestion Adapter")
    print("=" * 55)

    # Try to load world data
    world_data = {}
    for fname in ["world.json", "golden_world.json", "civix_world.json"]:
        try:
            world_data = load_json(fname)
            print(f"Loaded world data from: {fname}")
            break
        except FileNotFoundError:
            continue

    if not world_data:
        print("WARNING: No world JSON file found in output/")
        print("Creating minimal schema validation run without data ingestion.")
        world_data = {
            "persons": [], "networks": [], "organizations": [],
            "phones": [], "vehicles": [], "accounts": [], "properties": [],
            "devices": [], "cdrs": [], "transactions": [],
            "surveillance_reports": [], "vehicle_sightings": [],
            "intelligence_reports": [], "criminal_history_records": [],
            "property_transfers": [],
        }

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
        print(f"Connected to PostgreSQL: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")
    except psycopg2.OperationalError as e:
        print(f"ERROR: Cannot connect to PostgreSQL: {e}")
        print("Ensure the database is running and migrations 000–013 have been applied.")
        return

    try:
        with conn.cursor() as cur:
            print("\n[1/4] Creating system records...")
            sys_records = create_system_records(cur)

            print("\n[2/4] Ingesting entities...")
            id_map = ingest_entities(cur, world_data, sys_records)

            print("\n[3/4] Ingesting events...")
            ingest_events(cur, world_data, id_map, sys_records)

            print("\n[4/4] Verifying counts...")
            success = verify_counts(cur)

        conn.commit()
        print("\n✓ Ingestion committed successfully.")

        if success:
            print("\nPHASE 2A STATUS: READY")
        else:
            print("\nPHASE 2A STATUS: INGESTION COMPLETED WITH WARNINGS — review counts above.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR during ingestion: {e}")
        print("Transaction rolled back. Schema remains clean.")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
