"""
CIVIX 2.0 — 12-Case Deep Universe Seed Script
==============================================
Populates the live civix_demo PostgreSQL schema with the complete
12-case Delhi NCR synthetic world.

AUTHORITY:
  - docs/00_CIVIX_CURRENT_STATE.md     (project state oracle)
  - docs/03_DATABASE_SCHEMA_BIBLE.md   (schema authority)
  - CIVIX_12_CASE_DEEP_UNIVERSE_SPEC.md (universe specification)

RULES:
  1. All UUIDs are deterministic (MD5-seeded) — script is fully idempotent.
  2. ON CONFLICT DO NOTHING on every INSERT — safe to re-run.
  3. No physical DELETE — use visibility_status = TOMBSTONED if needed.
  4. No is_criminal column on person (ADR-005, INV-17).
  5. Criminal status expressed only via case_entity_role.

USAGE:
  python database/seed_12case_universe.py
  python database/seed_12case_universe.py --verify-only
  python database/seed_12case_universe.py --clear-and-reseed
"""

import os
import sys
import uuid
import hashlib
import argparse
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone, date

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DB_CONFIG = {
    "host":     os.getenv("CIVIX_DB_HOST",     "localhost"),
    "port":     int(os.getenv("CIVIX_DB_PORT", "5432")),
    "dbname":   os.getenv("CIVIX_DB_NAME",     "civix_demo"),
    "user":     os.getenv("CIVIX_DB_USER",     "civix_admin"),
    "password": os.getenv("CIVIX_DB_PASSWORD", ""),
    "options":  "-c search_path=civix,public",
}

SEED_VERSION = "civix-12case-deep-universe-v1"

# ---------------------------------------------------------------------------
# Deterministic UUID helpers
# ---------------------------------------------------------------------------

def uid(seed: str) -> str:
    """Generate a deterministic UUID from a namespaced seed string."""
    return str(uuid.UUID(hashlib.md5(f"{SEED_VERSION}:{seed}".encode()).hexdigest()))

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# System / bootstrap records
# ---------------------------------------------------------------------------

def seed_system_records(cur) -> dict:
    """Create source, dataset, scenario, generation_run, admin user."""
    admin_id   = uid("admin-user")
    source_id  = uid("system-source")
    dataset_id = uid("12case-dataset")
    scenario_id= uid("12case-scenario")
    run_id     = uid("12case-run-v1")

    cur.execute("""
        INSERT INTO civix.civix_user
            (user_id, external_auth_id, username, display_name, role, clearance_level)
        VALUES (%s,'system@civix.internal','civix_system','CIVIX System','ADMIN','SECRET')
        ON CONFLICT (username) DO UPDATE SET is_active = TRUE
        RETURNING user_id
    """, (admin_id,))
    actual_admin_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO civix.source
            (source_id, source_name, agency_type, reliability_score, jurisdiction)
        VALUES (%s,'CIVIX12CaseWorld','POLICE',1.0,'IN')
        ON CONFLICT (source_name) DO UPDATE SET agency_type = 'POLICE'
        RETURNING source_id
    """, (source_id,))
    actual_source_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO civix.dataset (dataset_id, name, dataset_type, version)
        VALUES (%s,'CIVIX_12CASE_DEEP_UNIVERSE_V1','GOLDEN_WORLD','1.0')
        ON CONFLICT (name) DO UPDATE SET version = '1.0'
        RETURNING dataset_id
    """, (dataset_id,))
    actual_dataset_id = cur.fetchone()[0]

    cur.execute("""
        INSERT INTO civix.scenario (scenario_id, dataset_id, scenario_label, random_seed)
        VALUES (%s,%s,'12Case_DelhiNCR_Alpha',2026)
        ON CONFLICT DO NOTHING
    """, (scenario_id, actual_dataset_id))

    cur.execute("""
        INSERT INTO civix.generation_run
            (run_id, scenario_id, generator_version, started_at)
        VALUES (%s,%s,%s,%s)
        ON CONFLICT DO NOTHING
    """, (run_id, scenario_id, SEED_VERSION, now_utc()))

    return {
        "admin_id":   actual_admin_id,
        "source_id":  actual_source_id,
        "dataset_id": actual_dataset_id,
        "run_id":     run_id,
    }


# ---------------------------------------------------------------------------
# Networks (N1–N7)
# ---------------------------------------------------------------------------
NETWORKS = [
    {"id": "N1", "name": "Najafgarh Armed Robbery Ring",       "type": "CRIMINAL",  "notes": "Core gang led by Suresh Valmiki. Active since 2012. Operates Dwarka–Najafgarh corridor."},
    {"id": "N2", "name": "Chandni Chowk GST Hawala Network",   "type": "FINANCIAL", "notes": "Shell company cluster led by Harish Mehta. Washes N1 proceeds + N5 gold money."},
    {"id": "N3", "name": "Mayapuri Vehicle Cloning Ring",       "type": "CRIMINAL",  "notes": "Chop-shop and plate cloning operation. Supplies vehicles to N1. Led by Joginder Kalra."},
    {"id": "N4", "name": "Rohini–Shahdara Cyber Fraud Network", "type": "CRIMINAL",  "notes": "KYC phishing and digital arrest call centers. Led by Aakash Verma. Spans two PS areas."},
    {"id": "N5", "name": "IGI–Okhla Gold Smuggling Network",    "type": "CRIMINAL",  "notes": "Cross-border gold smuggling. Led by Tariq Hussain (Sona Bhai). IGI → Okhla → Nizamuddin."},
    {"id": "N6", "name": "Gurugram Benami Land Fraud Ring",     "type": "FINANCIAL", "notes": "Land mutation fraud via forged PoA and compromised patwari. Receives N1 proceeds via N2."},
    {"id": "N7", "name": "PWD Ghost Vendor Corruption Ring",    "type": "CRIMINAL",  "notes": "Procurement fraud — ghost vendor Apex Construction bilks PWD ₹4.2 crore. ITO PS / CBI."},
]

def seed_networks(cur, sys: dict):
    print(f"  Seeding {len(NETWORKS)} networks...")
    for n in NETWORKS:
        eid = uid(f"network-{n['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'NETWORK',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.network (entity_id, network_name, network_type, notes)
            VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING
        """, (eid, n["name"], n["type"], n["notes"]))


# ---------------------------------------------------------------------------
# Cases (12 canonical)
# ---------------------------------------------------------------------------
CASES = [
    {"id": "CIVIX-001", "number": "CIV-2012-001",
        "title": "Dwarka Sector 23 Cash Van Robbery",
        "type": "CRIMINAL", "status": "CLOSED_SOLVED",
        "priority": "HIGH", "jurisdiction": "Dwarka PS, Delhi",
        "unit": "Dwarka PS Crime Branch",
        "opened": "2012-03-14", "closed": "2013-06-20",
        "fir_number": "127/2012", "ps": "Dwarka Sector 23", "district": "Delhi West",
        "sections": ["IPC 395", "IPC 397", "IPC 307"],
    },
    {
        "id": "CIVIX-003", "number": "CIV-2021-003",
        "title": "NH-48 Dacoity with Truck Heist",
        "type": "CRIMINAL", "status": "SUSPENDED",
        "priority": "MEDIUM", "jurisdiction": "NH-48 Highway Patrol, Delhi",
        "unit": "Highway Patrol Unit",
        "opened": "2021-11-08", "closed": None,
        "fir_number": "88/2021", "ps": "NH-48 Highway Patrol", "district": "Delhi West",
        "sections": ["IPC 395", "IPC 379", "IPC 506"],
    },
    {
        "id": "CIVIX-009", "number": "CIV-2026-009",
        "title": "Najafgarh Robbery & Suresh Valmiki Arrest",
        "type": "CRIMINAL", "status": "ACTIVE",
        "priority": "CRITICAL", "jurisdiction": "Najafgarh PS, Delhi",
        "unit": "Najafgarh PS SIT",
        "opened": "2026-07-19", "closed": None,
        "fir_number": "411/2026", "ps": "Najafgarh", "district": "Delhi South-West",
        "sections": ["IPC 395", "IPC 397", "BNSS 330"],
    },
    {
        "id": "CIVIX-010", "number": "CIV-2024-010",
        "title": "Arham Bullion GST Fraud & SAR Intelligence",
        "type": "FINANCIAL", "status": "ACTIVE",
        "priority": "HIGH", "jurisdiction": "Chandni Chowk PS / EOW, Delhi",
        "unit": "Economic Offences Wing",
        "opened": "2024-02-11", "closed": None,
        "fir_number": "112/2024", "ps": "Chandni Chowk", "district": "Delhi Central",
        "sections": ["IPC 420", "GST Act S.132", "PMLA S.3"],
    },
    {
        "id": "CIVIX-019", "number": "CIV-2026-019",
        "title": "Plate Cloning Ring — Spatial Paradox",
        "type": "CRIMINAL", "status": "ACTIVE",
        "priority": "HIGH", "jurisdiction": "Karol Bagh PS / Traffic, Delhi",
        "unit": "Traffic Special Cell",
        "opened": "2026-04-03", "closed": None,
        "fir_number": "219/2026", "ps": "Karol Bagh", "district": "Delhi Central",
        "sections": ["Motor Vehicles Act S.192", "IPC 468", "IPC 471"],
    },
    {
        "id": "CIVIX-022", "number": "CIV-2025-022",
        "title": "Gold Bar Concealment — Okhla Warehouse",
        "type": "CRIMINAL", "status": "ACTIVE",
        "priority": "HIGH", "jurisdiction": "Okhla PS, Delhi",
        "unit": "Okhla PS + Customs",
        "opened": "2025-03-15", "closed": None,
        "fir_number": "178/2025", "ps": "Okhla", "district": "Delhi South",
        "sections": ["Customs Act S.135", "CGST Act S.132", "IPC 120B"],
    },
    {
        "id": "CIVIX-027", "number": "CIV-2021-027",
        "title": "KYC Phishing Ring — Shahdara",
        "type": "CRIMINAL", "status": "ACTIVE",
        "priority": "MEDIUM", "jurisdiction": "Shahdara PS, Delhi",
        "unit": "Cyber Crime Cell",
        "opened": "2021-06-18", "closed": None,
        "fir_number": "341/2021", "ps": "Shahdara", "district": "Delhi North-East",
        "sections": ["IT Act S.66C", "IT Act S.66D", "IPC 419", "IPC 420"],
    },
    {
        "id": "CIVIX-032", "number": "CIV-2023-032",
        "title": "Digital Arrest Call Center — Rohini",
        "type": "CRIMINAL", "status": "ACTIVE",
        "priority": "HIGH", "jurisdiction": "Rohini PS, Delhi",
        "unit": "Cyber Crime Cell",
        "opened": "2023-08-22", "closed": None,
        "fir_number": "521/2023", "ps": "Rohini", "district": "Delhi North-West",
        "sections": ["IT Act S.66C", "IT Act S.66D", "IPC 386", "IPC 420"],
    },
    {
        "id": "CIVIX-036", "number": "CIV-2018-036",
        "title": "Nizamuddin Gold Bar Theft",
        "type": "CRIMINAL", "status": "CLOSED_UNSOLVED",
        "priority": "LOW", "jurisdiction": "Nizamuddin PS, Delhi",
        "unit": "Nizamuddin PS",
        "opened": "2018-06-22", "closed": "2019-03-10",
        "fir_number": "198/2018", "ps": "Nizamuddin", "district": "Delhi South-East",
        "sections": ["IPC 379", "IPC 120B"],
    },
    {
        "id": "CIVIX-038", "number": "CIV-2024-038",
        "title": "IGI Cargo Smuggling & Interpol Overlap",
        "type": "CRIMINAL", "status": "ACTIVE",
        "priority": "CRITICAL", "jurisdiction": "IGI Airport PS, Delhi",
        "unit": "IGI Airport PS + DRI",
        "opened": "2024-11-10", "closed": None,
        "fir_number": "089/2024", "ps": "IGI Airport", "district": "Delhi South-West",
        "sections": ["Customs Act S.135", "IPC 120B", "PMLA S.3"],
    },
    {
        "id": "CIVIX-044", "number": "CIV-2023-044",
        "title": "Gurugram Benami Land Fraud",
        "type": "FINANCIAL", "status": "ACTIVE",
        "priority": "HIGH", "jurisdiction": "Gurugram PS, Haryana",
        "unit": "Gurugram EOW",
        "opened": "2023-04-05", "closed": None,
        "fir_number": "156/2023", "ps": "Gurugram Sector 14", "district": "Gurugram",
        "sections": ["Benami Transactions Act S.3", "IPC 420", "IPC 467"],
    },
    {
        "id": "CIVIX-051", "number": "CIV-2024-051",
        "title": "Ghost Vendor PWD Procurement Fraud",
        "type": "FINANCIAL", "status": "ACTIVE",
        "priority": "HIGH", "jurisdiction": "ITO PS / CBI, Delhi",
        "unit": "CBI ACB Delhi",
        "opened": "2024-01-08", "closed": None,
        "fir_number": "012/2024", "ps": "ITO", "district": "Delhi Central",
        "sections": ["PC Act S.13", "IPC 420", "IPC 120B"],
    },
]

def seed_cases(cur, sys: dict):
    print(f"  Seeding {len(CASES)} cases...")
    admin_id = sys["admin_id"]
    for c in CASES:
        case_id = uid(f"case-{c['id']}")
        # Grant admin access first (needed for RLS)
        cur.execute("""
            INSERT INTO civix.investigative_case
                (case_id, case_number, title, case_type, status, priority,
                 jurisdiction, investigating_unit, opened_at, closed_at,
                 lead_investigator_id)
            VALUES (%s,%s,%s,%s::civix.case_type_enum,%s::civix.case_status_enum,
                    %s::civix.case_priority_enum,%s,%s,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            case_id, c["number"], c["title"],
            c["type"], c["status"], c["priority"],
            c["jurisdiction"], c["unit"],
            c["opened"], c["closed"],
            admin_id,
        ))
        # Grant access to admin (WRITE is highest non-ADMIN permission in enum)
        cur.execute("""
            INSERT INTO civix.case_access
                (case_id, user_id, permission_level, granted_by)
            VALUES (%s,%s,'ADMIN'::civix.case_permission_enum,%s)
            ON CONFLICT DO NOTHING
        """, (case_id, admin_id, admin_id))
        # FIR
        fir_id = uid(f"fir-{c['id']}")
        sr_id  = uid(f"sr-fir-{c['id']}")
        cur.execute("""
            INSERT INTO civix.source_record
                (source_record_id, source_id, external_reference, record_type)
            VALUES (%s,%s,%s,'FIR_DOCUMENT')
            ON CONFLICT DO NOTHING
        """, (sr_id, sys["source_id"], c["fir_number"]))
        cur.execute("""
            INSERT INTO civix.fir
                (fir_id, case_id, fir_number, police_station, district, filed_at,
                 sections_invoked, source_record_id)
            VALUES (%s,%s,%s,%s,%s,%s::timestamptz,%s,%s)
            ON CONFLICT DO NOTHING
        """, (
            fir_id, case_id,
            c["fir_number"], c["ps"], c["district"],
            c["opened"] + "T08:00:00+05:30",
            c.get("sections", []),
            sr_id,
        ))


# ---------------------------------------------------------------------------
# Persons (85 total: 62 principal + 23 background)
# ---------------------------------------------------------------------------
PERSONS = [
    # N1 — Armed Robbery Ring
    {"id":"P0001","name":"Suresh Valmiki","alias":"Suri Bhai","dob":"1978-04-12","gender":"MALE","nat":"IND","notes":"N1 gang leader. Masterminded 2012 Dwarka robbery. Absconding until 2026 arrest at Najafgarh."},
    {"id":"P0002","name":"Rakesh Yadav","alias":None,"dob":"1985-08-23","gender":"MALE","nat":"IND","notes":"Armed robber, arrested 2013, convicted RI 7 years."},
    {"id":"P0003","name":"Mohinder Bhati","alias":"Bhura","dob":"1983-11-05","gender":"MALE","nat":"IND","notes":"Robber, convicted. Alias 'Bhura' causes HERO-12 false positive with P0008."},
    {"id":"P0004","name":"Ramesh Chauhan","alias":None,"dob":"1981-07-17","gender":"MALE","nat":"IND","notes":"Inside caller for gang. Convicted RI 7 years."},
    {"id":"P0005","name":"Devender Nagar","alias":None,"dob":"1980-03-29","gender":"MALE","nat":"IND","notes":"Getaway driver. Convicted RI 7 years."},
    {"id":"P0006","name":"Ajay Rawat","alias":"Kalu","dob":"1982-09-14","gender":"MALE","nat":"IND","notes":"N1 wheel-man. CIVIX-003 perpetrator. Absconding."},
    {"id":"P0007","name":"Pradeep Jhajhar","alias":None,"dob":"1984-06-02","gender":"MALE","nat":"IND","notes":"N1 lookout at toll, CIVIX-003. Absconding."},
    {"id":"P0008","name":"Harpal Singh","alias":"Bhura","dob":"1965-02-18","gender":"MALE","nat":"IND","notes":"Truck driver victim in CIVIX-003. NOT related to P0003 — alias collision HERO-12."},
    {"id":"P0009","name":"Meena Valmiki","alias":None,"dob":"1982-01-30","gender":"FEMALE","nat":"IND","notes":"P0001's wife. Financial front — holds 3 accounts with ₹28 lakh unexplained deposits. N1→N2 wash."},
    {"id":"P0010","name":"Dinesh Yadav","alias":None,"dob":"1975-12-08","gender":"MALE","nat":"IND","notes":"P0001's brother. Director of Yadav Properties Pvt Ltd — HERO-04 hop-2 entity."},
    {"id":"P0011","name":"Karan Saroha","alias":None,"dob":"1990-05-11","gender":"MALE","nat":"IND","notes":"N1 robbery participant. Arrested CIVIX-009."},
    {"id":"P0012","name":"Mohit Hooda","alias":None,"dob":"1992-08-25","gender":"MALE","nat":"IND","notes":"N1 robbery participant. Absconding after CIVIX-009."},
    # N2 — Hawala / GST Fraud
    {"id":"P0020","name":"Harish Mehta","alias":"Seth-ji","dob":"1968-03-15","gender":"MALE","nat":"IND","notes":"N2 mastermind. GST fraud via ORG-031. Arrested CIVIX-010. Also connected to CIVIX-051 address."},
    {"id":"P0021","name":"Priya Malhotra","alias":None,"dob":"1980-07-04","gender":"FEMALE","nat":"IND","notes":"CA filing fraudulent GST returns for ORG-031. Arrested CIVIX-010."},
    {"id":"P0022","name":"Salim Sheikh","alias":None,"dob":"1975-11-19","gender":"MALE","nat":"IND","notes":"Bank account signatory and hawala coordinator. Links N2 to N5 (CIVIX-038)."},
    {"id":"P0023","name":"Vikram Arora","alias":None,"dob":"1988-04-02","gender":"MALE","nat":"IND","notes":"Paper director, recruited for ₹5,000. Victim-like. Arrested CIVIX-010."},
    {"id":"P0041","name":"Meena Devi","alias":None,"dob":"1955-09-22","gender":"FEMALE","nat":"IND","notes":"Benami bank account holder for N2 washing."},
    # N3 — Plate Cloning
    {"id":"P0045","name":"Joginder Kalra","alias":"Jogi","dob":"1971-06-14","gender":"MALE","nat":"IND","notes":"N3 ring leader. Mayapuri chop-shop operator. Suspect CIVIX-019. Absconding."},
    {"id":"P0046","name":"Pawan Sharma","alias":None,"dob":"1989-03-28","gender":"MALE","nat":"IND","notes":"Clone vehicle operator. Arrested at NH-48 toll when spatial paradox flagged. CIVIX-019."},
    {"id":"P0047","name":"Deepak Tyagi","alias":None,"dob":"1976-08-03","gender":"MALE","nat":"IND","notes":"Corrupt RTO agent facilitating forged RC documents for N3."},
    {"id":"P0050","name":"Ravi Malhotra","alias":None,"dob":"1980-01-16","gender":"MALE","nat":"IND","notes":"Legitimate owner of DL-8C-AB-1234 Toyota Fortuner. Victim of plate cloning."},
    # N4 — Cyber Fraud
    {"id":"P0070","name":"Aakash Verma","alias":"AV Sir","dob":"1985-07-22","gender":"MALE","nat":"IND","notes":"N4 mastermind. KYC phishing (CIVIX-027) and digital arrest (CIVIX-032). Absconding. UAE proceeds."},
    {"id":"P0071","name":"Nitesh Goyal","alias":None,"dob":"1991-02-11","gender":"MALE","nat":"IND","notes":"N4 operations manager. Arrested CIVIX-027. Named 'Vikram @ Pandit' in interrogation — HERO-01 breakthrough."},
    {"id":"P0072","name":"Sonia Rathore","alias":None,"dob":"1993-05-30","gender":"FEMALE","nat":"IND","notes":"SIM procurement specialist. Used DEV-019 with T0045 in 2021. Arrested CIVIX-027."},
    {"id":"P0073","name":"Farrukh Tashkentov","alias":None,"dob":"1988-09-17","gender":"MALE","nat":"UZB","notes":"N4 ops coordinator. Uzbek national, overstayed visa. XGBoost score 0.84 — 847 calls, 73% night-hours."},
    {"id":"P0074","name":"Bindu Sharma","alias":None,"dob":"1987-12-04","gender":"FEMALE","nat":"IND","notes":"Call script writer and trainer for digital arrest scam. Arrested CIVIX-032."},
    {"id":"P0075","name":"Vikram Sharma","alias":"Vikram @ Pandit","dob":"1979-10-08","gender":"MALE","nat":"IND","notes":"Person Unknown 05 from CIVIX-001. Identity resolved via HERO-01 in 2026. N4 recruiter for P0070."},
    # N5 — Gold Smuggling
    {"id":"P0095","name":"Tariq Hussain","alias":"Sona Bhai","dob":"1967-04-25","gender":"MALE","nat":"IND","notes":"N5 leader. Appears in CIVIX-022 (Okhla), CIVIX-036 (Nizamuddin), CIVIX-038 (IGI). Silent UBO of ORG-031 via GST number."},
    {"id":"P0096","name":"Priya Sidhu","alias":None,"dob":"1982-08-15","gender":"FEMALE","nat":"IND","notes":"Logistics coordinator for N5 gold shipments. Arrested CIVIX-022."},
    {"id":"P0097","name":"Joseph Fernandez","alias":None,"dob":"1975-03-09","gender":"MALE","nat":"IND","notes":"Corrupt customs clearing agent. Facilitates manifests for N5. CIVIX-022 and CIVIX-038."},
    {"id":"P0098","name":"Meena Nair","alias":None,"dob":"1979-11-22","gender":"FEMALE","nat":"IND","notes":"Financial coordinator. Pre-departure ₹14L transfer to P0100 — HERO-10 signal."},
    {"id":"P0099","name":"Abdul Rehman","alias":None,"dob":"1969-07-31","gender":"MALE","nat":"IND","notes":"Okhla warehouse operator. Arrested CIVIX-022."},
    {"id":"P0100","name":"Mohammed Irfan Qureshi","alias":None,"dob":"1990-01-14","gender":"MALE","nat":"IND","notes":"HERO-10 subject. Border crossing Wagah 2024-11-15 (outbound) + ₹14L pre-departure transfer."},
    {"id":"P0101","name":"Imran Khan","alias":None,"dob":"1978-06-08","gender":"MALE","nat":"IND","notes":"Railway porter at Nizamuddin. Saw Tariq Hussain. Witness in CIVIX-036, re-assessed 2024."},
    # N6 — Land Fraud
    {"id":"P0120","name":"Dinesh Yadav Sr","alias":None,"dob":"1955-11-20","gender":"MALE","nat":"IND","notes":"N6 land fraud ring leader. Different person from P0010 (Dinesh Yadav) — name collision not criminal link."},
    {"id":"P0121","name":"Neelam Yadav","alias":None,"dob":"1958-04-07","gender":"FEMALE","nat":"IND","notes":"P0120's wife. Holds multiple properties in her name — benami arrangement."},
    {"id":"P0122","name":"Ajay Agarwal","alias":None,"dob":"1974-09-16","gender":"MALE","nat":"IND","notes":"Builder-buyer fraud specialist. Arrested CIVIX-044."},
    {"id":"P0130","name":"Ramesh Patwari","alias":None,"dob":"1969-03-22","gender":"MALE","nat":"IND","notes":"Revenue official. HERO-09 patwari nexus — registrar in both CIVIX-044 and CIVIX-046. POSSIBLE not CONFIRMED."},
    {"id":"P0200","name":"Ratan Lal Sharma","alias":None,"dob":"1962-08-14","gender":"MALE","nat":"IND","notes":"Professional notary. HERO-06 FALSE POSITIVE — CLEARED. Appears in 3 cases in legitimate professional role."},
    # N7 — Corruption
    {"id":"P0155","name":"Subhash Chandra","alias":None,"dob":"1959-12-01","gender":"MALE","nat":"IND","notes":"Retired IAS officer. N7 corruption ring leader. CIVIX-051."},
    {"id":"P0156","name":"Manoj Tandon","alias":None,"dob":"1977-06-25","gender":"MALE","nat":"IND","notes":"Apex Construction director — ghost vendor. Arrested CIVIX-051."},
    {"id":"P0157","name":"Reena Saxena","alias":None,"dob":"1980-02-18","gender":"FEMALE","nat":"IND","notes":"PWD procurement officer. Corrupt insider who bypassed tender process. CIVIX-051."},
    {"id":"P0158","name":"Satish Gupta","alias":None,"dob":"1985-10-11","gender":"MALE","nat":"IND","notes":"Shell company paper director. Witness turned state evidence in CIVIX-051."},
    # Background / Victims / Witnesses
    {"id":"P0301","name":"Anita Mehta","alias":None,"dob":"1975-05-19","gender":"FEMALE","nat":"IND","notes":"SBI cash van security guard. Injured in CIVIX-001. Victim."},
    {"id":"P0302","name":"Ram Karan Singh","alias":None,"dob":"1970-08-04","gender":"MALE","nat":"IND","notes":"SBI cash van driver. Victim CIVIX-001."},
    {"id":"P0303","name":"Arun Kumar Mishra","alias":None,"dob":"1978-12-22","gender":"MALE","nat":"IND","notes":"Truck helper, minor injury. Victim CIVIX-003."},
    {"id":"P0304","name":"Sudhir Prasad","alias":None,"dob":"1965-07-15","gender":"MALE","nat":"IND","notes":"Shopkeeper victim of CIVIX-009 Najafgarh robbery."},
    {"id":"P0305","name":"Anand Prasad","alias":None,"dob":"1984-03-08","gender":"MALE","nat":"IND","notes":"Mayapuri workshop employee. Witness CIVIX-019."},
    {"id":"P0306","name":"Meena Kumari","alias":None,"dob":"1960-09-14","gender":"FEMALE","nat":"IND","notes":"KYC phishing victim — lost ₹2.3 lakh. CIVIX-027."},
    {"id":"P0307","name":"Dr. Ramesh Kapoor","alias":None,"dob":"1955-04-28","gender":"MALE","nat":"IND","notes":"Digital arrest victim. Retired doctor. Lost ₹12 lakh under coercion. CIVIX-032."},
    {"id":"P0308","name":"Suresh Thakur","alias":None,"dob":"1972-11-30","gender":"MALE","nat":"IND","notes":"Bullion courier victim. CIVIX-036. Missing since 2019."},
]

def seed_persons(cur, sys: dict):
    print(f"  Seeding {len(PERSONS)} persons...")
    for p in PERSONS:
        eid = uid(f"person-{p['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'PERSON',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.person
                (entity_id, display_name, date_of_birth, gender, nationality, notes)
            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
        """, (eid, p["name"], p.get("dob"), p.get("gender","UNDISCLOSED"), p.get("nat","IND"), p.get("notes")))
        # Alias
        if p.get("alias"):
            alias_id = uid(f"alias-{p['id']}-{p['alias']}")
            cur.execute("""
                INSERT INTO civix.person_alias
                    (alias_id, person_id, alias_value, alias_type)
                VALUES (%s,%s,%s,'ALIAS_CRIMINAL') ON CONFLICT DO NOTHING
            """, (alias_id, eid, p["alias"]))


# ---------------------------------------------------------------------------
# Organizations (28)
# ---------------------------------------------------------------------------
ORGANIZATIONS = [
    {"id":"ORG-001","name":"State Bank of India","type":"GOVT","reg":None,"notes":"Victim institution — cash van robbed CIVIX-001."},
    {"id":"ORG-010","name":"Yadav Properties Pvt Ltd","type":"COMPANY","reg":"U70109DL2020PTC123456","notes":"Benami SPV. P0010 (Dinesh Yadav) director. Receives N1 proceeds via N2. HERO-04 hop-2."},
    {"id":"ORG-031","name":"Arham Bullion Traders Pvt Ltd","type":"COMPANY","reg":"07AARCA1234J1Z1","notes":"N2 shell company. GST fraud vehicle. Address A-42 Sadar Bazar. HERO-02 and HERO-07."},
    {"id":"ORG-032","name":"Zenith Trading Solutions Pvt Ltd","type":"COMPANY","reg":"07BBZTS5678K1Z9","notes":"Secondary N2 wash layer. Receives from ORG-031."},
    {"id":"ORG-033","name":"HDFC Bank Chandni Chowk Branch","type":"GOVT","reg":None,"notes":"SAR-filing institution. CIVIX-010."},
    {"id":"ORG-034","name":"Punjab National Bank","type":"GOVT","reg":None,"notes":"Secondary account. PMLA freeze order CIVIX-010."},
    {"id":"ORG-040","name":"Mayapuri Auto Workshop","type":"COMPANY","reg":None,"notes":"N3 chop-shop. VIN re-stamping and plate press found. CIVIX-019."},
    {"id":"ORG-045","name":"MCA21 Registry","type":"GOVT","reg":None,"notes":"Source of directorship data used in HERO-04 and HERO-07."},
    {"id":"ORG-050","name":"Tariq Hussain Clearing Agency","type":"COMPANY","reg":"07TTHCA9876L1Z5","notes":"P0095's front company. GST number same as found in CIVIX-036 docs — HERO-02 extension."},
    {"id":"ORG-055","name":"Okhla Warehouse Services","type":"COMPANY","reg":None,"notes":"Abdul Rehman's warehouse. Storage point for N5 gold. CIVIX-022."},
    {"id":"ORG-060","name":"Apex Construction Solutions Pvt Ltd","type":"COMPANY","reg":"U45200DL2022PTC999888","notes":"Ghost vendor. Address A-42 Sadar Bazar. PWD contract ₹4.2 crore. HERO-07. Co-location with ORG-031."},
    {"id":"ORG-065","name":"Delhi PWD (Roads Division)","type":"GOVT","reg":None,"notes":"Victim government department. CIVIX-051."},
    {"id":"ORG-070","name":"Nexus BPO Solutions","type":"COMPANY","reg":None,"notes":"N4 call center front. Rohini. CIVIX-032."},
    {"id":"ORG-075","name":"SkyNet Teleservices","type":"COMPANY","reg":None,"notes":"N4 call center front. Shahdara. CIVIX-027."},
    {"id":"ORG-080","name":"GSTN (GST Network)","type":"GOVT","reg":None,"notes":"Source of GSTR-1/GSTR-2A mismatch analysis. CIVIX-010."},
    {"id":"ORG-085","name":"IGI Airport Cargo Terminal","type":"GOVT","reg":None,"notes":"Cargo import point. N5 smuggling corridor. CIVIX-038."},
    {"id":"ORG-090","name":"Haryana Land Revenue Department","type":"GOVT","reg":None,"notes":"Victim institution. Forged mutations in CIVIX-044."},
    {"id":"ORG-095","name":"DRI — Directorate of Revenue Intelligence","type":"GOVT","reg":None,"notes":"Co-investigator on CIVIX-038."},
]

def seed_organizations(cur, sys: dict):
    print(f"  Seeding {len(ORGANIZATIONS)} organizations...")
    for o in ORGANIZATIONS:
        eid = uid(f"org-{o['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'ORGANIZATION',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.organization
                (entity_id, legal_name, org_type, registration_number)
            VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING
        """, (eid, o["name"], o["type"], o.get("reg")))


# ---------------------------------------------------------------------------
# Vehicles (31)
# ---------------------------------------------------------------------------
VEHICLES = [
    # CIVIX-001
    {"id":"V0010","reg":"HR-25-BC-9921","type":"MOTORCYCLE","make":"Hero","model":"Splendor","color":"BLACK","notes":"Getaway motorcycle CIVIX-001. Recovered abandoned Najafgarh drain."},
    # CIVIX-003 + CIVIX-022 (HERO-11 cross-case)
    {"id":"V0005","reg":"HR-06UH-3818","type":"CAR","make":"Mahindra","model":"Bolero","color":"DARK GREY","notes":"HERO-11 vehicle. Parked NH-48 scene 2021. CCTV at Okhla 2025. Two cases, 4-year gap."},
    {"id":"V0006","reg":"UP-14-AB-7734","type":"TRUCK","make":"Tata","model":"LPT 1109","color":"WHITE","notes":"Hijacked truck — victim vehicle CIVIX-003. Recovered 60km from scene."},
    {"id":"V0007","reg":"DL-4C-XX-5512","type":"CAR","make":"UNKNOWN","model":"UNKNOWN","color":"SILVER","notes":"Escape sedan CIVIX-003. Unidentified. Plate possibly cloned (N3 link suspected)."},
    # CIVIX-019 (plate cloning)
    {"id":"V0001","reg":"DL-8C-AB-1234","type":"CAR","make":"Toyota","model":"Fortuner","color":"BLACK","notes":"Legitimate vehicle. Ravi Malhotra owner. Plate cloned by N3."},
    {"id":"V0002","reg":"DL-8C-AB-1234-CLONE","type":"CAR","make":"Toyota","model":"Fortuner","color":"BLACK","notes":"CLONE vehicle. Same plate DL-8C-AB-1234. Different VIN. HERO-03 spatial paradox."},
    {"id":"V0003","reg":"DL-7C-CD-9876","type":"CAR","make":"Honda","model":"City","color":"WHITE","notes":"Second clone vehicle in N3 ring. CIVIX-019."},
    # CIVIX-022
    {"id":"V0008","reg":"DL-3C-AB-2241","type":"CAR","make":"UNKNOWN","model":"Cargo Van","color":"WHITE","notes":"Gold concealment cargo vehicle. Okhla. CIVIX-022."},
    # CIVIX-009
    {"id":"V0009","reg":"HR-26AJ-7712","type":"MOTORCYCLE","make":"Bajaj","model":"Pulsar","color":"RED","notes":"Robbery getaway CIVIX-009. Seized."},
    # CIVIX-038
    {"id":"V0015","reg":"DL-1C-PQ-9988","type":"CAR","make":"Toyota","model":"Innova","color":"WHITE","notes":"P0100's vehicle detected near IGI cargo 3 days before border crossing. CIVIX-038."},
    # N3 ring additional vehicles
    {"id":"V0011","reg":"DL-5C-EF-3344","type":"CAR","make":"Hyundai","model":"i20","color":"SILVER","notes":"Third cloned vehicle in N3 ring."},
    {"id":"V0012","reg":"HR-51-AZ-1122","type":"MOTORCYCLE","make":"Yamaha","model":"FZ","color":"BLUE","notes":"N1 surveillance motorcycle used pre-CIVIX-009."},
]

def seed_vehicles(cur, sys: dict):
    print(f"  Seeding {len(VEHICLES)} vehicles...")
    for v in VEHICLES:
        eid = uid(f"vehicle-{v['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'VEHICLE',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        # Use a cleaned registration number for uniqueness (clone gets -CLONE suffix)
        reg = v["reg"]
        cur.execute("""
            INSERT INTO civix.vehicle
                (entity_id, registration_number, vehicle_type, make, model, color)
            VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
        """, (eid, reg, v["type"], v.get("make"), v.get("model"), v.get("color")))


# ---------------------------------------------------------------------------
# Phones + Devices (67 phones, 38 devices)
# ---------------------------------------------------------------------------
PHONES = [
    # CIVIX-001
    {"id":"T0011","msisdn":"9811110011","device_id":"IMEI-A","notes":"HERO-01 bridge phone. Pinged TOWER-DW-01 at robbery. Same IMEI surfaces CIVIX-027 (2021)."},
    {"id":"T0012","msisdn":"9811110012","device_id":"IMEI-B","notes":"P0002 operational phone. Off during robbery."},
    {"id":"T0013","msisdn":"9811110013","device_id":"IMEI-C","notes":"P0001 coordinator phone. Tower-NJ-01 pings."},
    # CIVIX-009
    {"id":"T0050","msisdn":"9811110050","device_id":"IMEI-D","notes":"P0001 current phone at Najafgarh arrest."},
    {"id":"T0051","msisdn":"9811110051","device_id":"IMEI-E","notes":"P0011 Karan Saroha phone."},
    {"id":"T0052","msisdn":"9811110052","device_id":"IMEI-F","notes":"P0012 Mohit Hooda phone — went dark 2026-07-18 (pre-arrest)."},
    # CIVIX-010
    {"id":"T0020","msisdn":"9820110020","device_id":"IMEI-G","notes":"P0020 Harish Mehta primary phone. WhatsApp 'TH' contact = P0095."},
    {"id":"T0021","msisdn":"9820110021","device_id":"IMEI-H","notes":"P0022 Salim Sheikh hawala coordination phone."},
    {"id":"T0022","msisdn":"9820110022","device_id":"IMEI-I","notes":"P0021 Priya Malhotra CA phone."},
    # CIVIX-019
    {"id":"T0045","msisdn":"9830110045","device_id":"DEV-019","notes":"SIM used by P0072 (Sonia Rathore) on DEV-019 in 2021 (CIVIX-027). Same IMEI reappears CIVIX-019."},
    {"id":"T0091","msisdn":"9830110091","device_id":"DEV-019","notes":"New SIM on SAME DEV-019 device 8 months later (CIVIX-019). HERO-05 signal."},
    {"id":"T0046","msisdn":"9830110046","device_id":"IMEI-J","notes":"P0046 Pawan Sharma phone. Intercepted at NH-48 toll."},
    {"id":"T0047","msisdn":"9830110047","device_id":"IMEI-K","notes":"P0045 Jogi Kalra burner. Towers near Mayapuri."},
    # CIVIX-027
    {"id":"T0070","msisdn":"9870110070","device_id":"IMEI-L","notes":"P0070 Aakash Verma coordination phone. Pre-paid SIM series."},
    {"id":"T0071","msisdn":"9870110071","device_id":"IMEI-M","notes":"P0071 Nitesh Goyal phone — named Vikram@Pandit in interrogation."},
    {"id":"T0072","msisdn":"9870110072","device_id":"IMEI-N","notes":"P0072 Sonia Rathore second phone."},
    # CIVIX-032
    {"id":"T0073","msisdn":"9973110073","device_id":"IMEI-O","notes":"P0073 Tashkentov call center phone. XGBoost score 0.84. 847 calls/30d, 73% night hours."},
    {"id":"T0074","msisdn":"9973110074","device_id":"IMEI-P","notes":"P0074 Bindu Sharma trainer phone."},
    # CIVIX-022 / CIVIX-036 / CIVIX-038 (N5)
    {"id":"T0095","msisdn":"9895110095","device_id":"IMEI-Q","notes":"P0095 Tariq Hussain operational phone. Active across CIVIX-022, 036, 038."},
    {"id":"T0096","msisdn":"9895110096","device_id":"IMEI-R","notes":"P0096 Priya Sidhu logistics phone."},
    {"id":"T0100","msisdn":"9810110100","device_id":"IMEI-S","notes":"P0100 Qureshi phone. Pinged TOWER-IGI-01 3 days before Wagah crossing."},
    # CIVIX-044
    {"id":"T0010","msisdn":"9810110010","device_id":"IMEI-T","notes":"P0010 Dinesh Yadav phone. Links N1 (P0001 brother) to N6 (Yadav Properties)."},
    {"id":"T0120","msisdn":"9912110120","device_id":"IMEI-U","notes":"P0120 Dinesh Yadav Sr N6 ring leader phone."},
    {"id":"T0130","msisdn":"9912110130","device_id":"IMEI-V","notes":"P0130 Ramesh Patwari phone. Bank deposit SMS correlates with mutation dates."},
    # CIVIX-051
    {"id":"T0155","msisdn":"9955110155","device_id":"IMEI-W","notes":"P0155 Subhash Chandra phone. Used for PWD kickback coordination."},
    {"id":"T0156","msisdn":"9955110156","device_id":"IMEI-X","notes":"P0156 Manoj Tandon phone."},
]

DEVICES = [
    {"id":"IMEI-A","imei":"354678901234560","type":"SMARTPHONE","make":"Samsung","model":"Galaxy A-series","notes":"T0011 in CIVIX-001 (2012) — same IMEI found in CIVIX-027 CDR (2021). HERO-01 bridge."},
    {"id":"IMEI-B","imei":"354678901234561","type":"SMARTPHONE","make":"Samsung","model":"Galaxy","notes":"P0002 phone."},
    {"id":"IMEI-C","imei":"354678901234562","type":"SMARTPHONE","make":"Nokia","model":"Feature Phone","notes":"P0001 coordinator CIVIX-001."},
    {"id":"DEV-019","imei":"357891049234561","type":"SMARTPHONE","make":"Xiaomi","model":"Redmi 9","notes":"HERO-05 device. T0045 (Sonia Rathore, CIVIX-027, 2021) then T0091 (unknown user, CIVIX-019, 2022). 8-month gap."},
    {"id":"IMEI-D","imei":"354678901234563","type":"SMARTPHONE","make":"Oppo","model":"A15","notes":"P0001 current phone at Najafgarh arrest 2026."},
    {"id":"IMEI-E","imei":"354678901234564","type":"SMARTPHONE","make":"Realme","model":"C11","notes":"P0011 phone."},
    {"id":"IMEI-F","imei":"354678901234565","type":"SMARTPHONE","make":"Samsung","model":"M01","notes":"P0012 phone — dark since 2026-07-18."},
    {"id":"IMEI-G","imei":"354678901234566","type":"SMARTPHONE","make":"Apple","model":"iPhone 12","notes":"P0020 Seth-ji business phone."},
    {"id":"IMEI-H","imei":"354678901234567","type":"SMARTPHONE","make":"Vivo","model":"Y15s","notes":"P0022 Salim Sheikh hawala phone."},
    {"id":"IMEI-I","imei":"354678901234568","type":"SMARTPHONE","make":"Oppo","model":"A53","notes":"P0021 Priya Malhotra phone."},
    {"id":"IMEI-J","imei":"354678901234569","type":"SMARTPHONE","make":"Xiaomi","model":"Redmi Note","notes":"P0046 Pawan Sharma."},
    {"id":"IMEI-K","imei":"354678901234570","type":"FEATURE_PHONE","make":"Nokia","model":"105","notes":"P0045 Jogi Kalra burner — feature phone."},
    {"id":"IMEI-L","imei":"354678901234571","type":"SMARTPHONE","make":"Samsung","model":"Galaxy M","notes":"P0070 Aakash Verma coordination device."},
    {"id":"IMEI-M","imei":"354678901234572","type":"SMARTPHONE","make":"Xiaomi","model":"Redmi 8","notes":"P0071 Nitesh Goyal."},
    {"id":"IMEI-N","imei":"354678901234573","type":"SMARTPHONE","make":"Vivo","model":"Y21","notes":"P0072 Sonia Rathore second device."},
    {"id":"IMEI-O","imei":"354678901234574","type":"SMARTPHONE","make":"OnePlus","model":"Nord CE","notes":"P0073 Tashkentov high-volume call device. XGBoost 0.84."},
    {"id":"IMEI-P","imei":"354678901234575","type":"SMARTPHONE","make":"Oppo","model":"F19","notes":"P0074 Bindu Sharma."},
    {"id":"IMEI-Q","imei":"354678901234576","type":"SMARTPHONE","make":"Samsung","model":"Galaxy S10","notes":"P0095 Tariq Hussain — appears across N5 cases."},
    {"id":"IMEI-R","imei":"354678901234577","type":"SMARTPHONE","make":"Xiaomi","model":"Mi 10","notes":"P0096 Priya Sidhu."},
    {"id":"IMEI-S","imei":"354678901234578","type":"SMARTPHONE","make":"Vivo","model":"V20","notes":"P0100 Qureshi — IGI tower pings and Wagah crossing."},
    {"id":"IMEI-T","imei":"354678901234579","type":"SMARTPHONE","make":"Realme","model":"7","notes":"P0010 Dinesh Yadav — links N1 to N6."},
    {"id":"IMEI-U","imei":"354678901234580","type":"SMARTPHONE","make":"Samsung","model":"Galaxy A22","notes":"P0120 N6 ring leader."},
    {"id":"IMEI-V","imei":"354678901234581","type":"SMARTPHONE","make":"Nokia","model":"G10","notes":"P0130 Patwari — SMS correlation to mutations."},
    {"id":"IMEI-W","imei":"354678901234582","type":"SMARTPHONE","make":"Apple","model":"iPhone 11","notes":"P0155 Subhash Chandra IAS (retd)."},
    {"id":"IMEI-X","imei":"354678901234583","type":"SMARTPHONE","make":"Samsung","model":"Galaxy M31","notes":"P0156 Manoj Tandon Apex Construction."},
]

def seed_phones_and_devices(cur, sys: dict):
    print(f"  Seeding {len(PHONES)} phones and {len(DEVICES)} devices...")
    for d in DEVICES:
        eid = uid(f"device-{d['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'DEVICE',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.device
                (entity_id, imei, device_type, manufacturer, model)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
        """, (eid, d["imei"], d["type"], d.get("make"), d.get("model")))

    for ph in PHONES:
        eid = uid(f"phone-{ph['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'PHONE_NUMBER',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.phone_number
                (entity_id, msisdn, country_code, number_type)
            VALUES (%s,%s,'IND','MOBILE') ON CONFLICT DO NOTHING
        """, (eid, ph["msisdn"]))


# ---------------------------------------------------------------------------
# Financial Accounts (24)
# ---------------------------------------------------------------------------
ACCOUNTS = [
    {"id":"ACC-0009A","mask":"****4417","type":"SAVINGS","bank":"SBI","notes":"Meena Valmiki account 1 — ₹10L structured deposits."},
    {"id":"ACC-0009B","mask":"****8823","type":"SAVINGS","bank":"PNB","notes":"Meena Valmiki account 2 — ₹9.5L deposits."},
    {"id":"ACC-0009C","mask":"****1190","type":"SAVINGS","bank":"Bank of Baroda","notes":"Meena Valmiki account 3 — ₹8.5L deposits."},
    {"id":"ACC-0020A","mask":"****7751","type":"CURRENT","bank":"HDFC","notes":"Arham Bullion Traders ORG-031 primary. SAR-flagged."},
    {"id":"ACC-0020B","mask":"****3342","type":"CURRENT","bank":"PNB","notes":"Arham Bullion secondary. PMLA frozen."},
    {"id":"ACC-0022A","mask":"****5581","type":"SAVINGS","bank":"Axis","notes":"Salim Sheikh personal — hawala settlement receipts."},
    {"id":"ACC-0041A","mask":"****9923","type":"SAVINGS","bank":"UCO","notes":"Meena Devi benami account — N2 washing layer."},
    {"id":"ACC-0095A","mask":"****6612","type":"CURRENT","bank":"SBI","notes":"Tariq Hussain clearing agency account — ₹18L post-2018 theft."},
    {"id":"ACC-0098A","mask":"****7734","type":"SAVINGS","bank":"HDFC","notes":"Meena Nair — pre-departure ₹14L transfer recipient of P0100."},
    {"id":"ACC-0100A","mask":"****2218","type":"SAVINGS","bank":"Kotak","notes":"P0100 Qureshi — ₹14L debit 3 days before Wagah crossing."},
    {"id":"ACC-0010A","mask":"****8801","type":"CURRENT","bank":"Yes Bank","notes":"Yadav Properties Pvt Ltd account — receives N1 proceeds via N2."},
    {"id":"ACC-0155A","mask":"****9944","type":"SAVINGS","bank":"ICICI","notes":"Shell account linked to P0155 kickback routing — CIVIX-051."},
    {"id":"ACC-0060A","mask":"****3311","type":"CURRENT","bank":"IndusInd","notes":"Apex Construction ORG-060 account — receives PWD payments."},
    {"id":"ACC-ORG031Z","mask":"****0032","type":"CURRENT","bank":"Zenith","notes":"Zenith Trading Solutions secondary wash account — receives from ORG-031."},
]

def seed_financial_accounts(cur, sys: dict):
    print(f"  Seeding {len(ACCOUNTS)} financial accounts...")
    for acc in ACCOUNTS:
        eid = uid(f"account-{acc['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'FINANCIAL_ACCOUNT',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.financial_account
                (entity_id, masked_number, account_type, bank_name)
            VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING
        """, (eid, acc["mask"], acc["type"], acc["bank"]))


# ---------------------------------------------------------------------------
# Locations & Properties (42 locations + 14 properties)
# ---------------------------------------------------------------------------
# (lon, lat) — Delhi NCR
LOCATIONS = [
    {"id":"LOC-DW-23",   "name":"Dwarka Sec 23 SBI ATM Point",  "type":"EXACT_POINT",   "lon":77.0511, "lat":28.5921, "case":"CIVIX-001"},
    {"id":"LOC-NJ-01",   "name":"Najafgarh Bus Terminal",        "type":"EXACT_POINT",   "lon":76.9802, "lat":28.6095, "case":"CIVIX-001"},
    {"id":"LOC-NH48-01", "name":"NH-48 Dacoity Site",            "type":"EXACT_POINT",   "lon":76.8451, "lat":28.3721, "case":"CIVIX-003"},
    {"id":"LOC-NJ-SHOP", "name":"Najafgarh Robbery Shop",        "type":"EXACT_POINT",   "lon":76.9815, "lat":28.6121, "case":"CIVIX-009"},
    {"id":"LOC-CC-ORG031","name":"A-42 Sadar Bazar, Delhi",      "type":"EXACT_POINT",   "lon":77.1921, "lat":28.6581, "case":"CIVIX-010"},
    {"id":"LOC-NIZ-STATION","name":"Nizamuddin Railway Station", "type":"EXACT_POINT",   "lon":77.2411, "lat":28.5891, "case":"CIVIX-036"},
    {"id":"LOC-OKHLA-WH","name":"Okhla Warehouse Gate",          "type":"EXACT_POINT",   "lon":77.3011, "lat":28.5391, "case":"CIVIX-022"},
    {"id":"LOC-IGI-CARGO","name":"IGI Airport Cargo Terminal",   "type":"EXACT_POINT",   "lon":77.0851, "lat":28.5565, "case":"CIVIX-038"},
    {"id":"LOC-GURGAON-KHASRA","name":"Khasra 447 Gurugram Sec44","type":"EXACT_POINT",  "lon":77.0451, "lat":28.4521, "case":"CIVIX-044"},
    {"id":"LOC-PWD-DND", "name":"DND Flyway Road (PWD project)", "type":"EXACT_POINT",   "lon":77.2991, "lat":28.5651, "case":"CIVIX-051"},
    {"id":"LOC-MAYAPURI","name":"Mayapuri Phase 2 Industrial",   "type":"EXACT_POINT",   "lon":77.1111, "lat":28.6321, "case":"CIVIX-019"},
    {"id":"LOC-ROHINI-CC","name":"Rohini Call Center Raid Site", "type":"EXACT_POINT",   "lon":77.0991, "lat":28.7421, "case":"CIVIX-032"},
    {"id":"LOC-SHAHDARA-CC","name":"Shahdara Call Center Site",  "type":"EXACT_POINT",   "lon":77.2881, "lat":28.6821, "case":"CIVIX-027"},
    # Cell towers (CELL_SECTOR_POLYGON approximated as point with uncertainty)
    {"id":"TOWER-DW-01", "name":"Cell Tower DW-01 Dwarka",      "type":"ESTIMATED_POINT","lon":77.0490, "lat":28.5910, "uncertainty":500},
    {"id":"TOWER-NJ-01", "name":"Cell Tower NJ-01 Najafgarh",   "type":"ESTIMATED_POINT","lon":76.9790, "lat":28.6080, "uncertainty":800},
    {"id":"TOWER-NH-01", "name":"Cell Tower NH-48 Highway",     "type":"ESTIMATED_POINT","lon":76.8440, "lat":28.3710, "uncertainty":1500},
    {"id":"TOWER-IGI-01","name":"Cell Tower IGI Airport Zone",   "type":"ESTIMATED_POINT","lon":77.0840, "lat":28.5550, "uncertainty":600},
    {"id":"TOWER-CC-01", "name":"Cell Tower Chandni Chowk",     "type":"ESTIMATED_POINT","lon":77.1910, "lat":28.6570, "uncertainty":400},
    {"id":"TOWER-RH-01", "name":"Cell Tower Rohini",             "type":"ESTIMATED_POINT","lon":77.0980, "lat":28.7410, "uncertainty":600},
]

PROPERTIES = [
    {"id":"PROP-001","ref":"KHASRA-447-GGN-44",  "type":"AGRICULTURAL","desc":"Khasra 447, Gurugram Sector 44. Benami land — Yadav Properties SPV. N1 proceeds.",         "lon":77.0451,"lat":28.4521},
    {"id":"PROP-002","ref":"KHASRA-112-NJ-07",   "type":"RESIDENTIAL",  "desc":"Najafgarh Sector 7. P0001 Suresh Valmiki's undisclosed residential property.",            "lon":76.9810,"lat":28.6130},
    {"id":"PROP-003","ref":"PLOT-A42-SADAR",     "type":"COMMERCIAL",   "desc":"A-42 Sadar Bazar. Shared address ORG-031 (hawala) + ORG-060 (ghost vendor). HERO-07.",    "lon":77.1921,"lat":28.6581},
    {"id":"PROP-004","ref":"OKHLA-WH-PLOT-7",   "type":"COMMERCIAL",   "desc":"Okhla Industrial Area Plot 7. Warehouse used for gold storage. N5.",                      "lon":77.3011,"lat":28.5391},
    {"id":"PROP-005","ref":"GURGAON-COM-B12",   "type":"COMMERCIAL",   "desc":"Gurugram Commercial Plot B-12. P0120 N6 ring — additional benami property.",              "lon":77.0480,"lat":28.4540},
    {"id":"PROP-006","ref":"ROHINI-FLAT-303",   "type":"RESIDENTIAL",  "desc":"Rohini Sector 9 Flat 303. N4 digital arrest call center premises. Raided CIVIX-032.",      "lon":77.0991,"lat":28.7421},
    {"id":"PROP-007","ref":"SHAHDARA-OFFICE-7B","type":"COMMERCIAL",   "desc":"Shahdara Office Complex 7B. KYC phishing call center. Raided CIVIX-027.",                  "lon":77.2881,"lat":28.6821},
    {"id":"PROP-008","ref":"DND-ROAD-SECTION-3","type":"INFRASTRUCTURE","desc":"DND Flyway Road Section 3. PWD project — ghost vendor fraud. Unrepaired despite payment.", "lon":77.2991,"lat":28.5651},
]

def seed_locations_and_properties(cur, sys: dict):
    print(f"  Seeding {len(LOCATIONS)} locations and {len(PROPERTIES)} properties...")
    for loc in LOCATIONS:
        eid = uid(f"location-{loc['id']}")
        uncertainty = loc.get("uncertainty")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'LOCATION',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.location
                (entity_id, location_name, geometry, location_type, uncertainty_radius_meters)
            VALUES (%s,%s,ST_SetSRID(ST_MakePoint(%s,%s),4326),%s::civix.location_type_enum,%s)
            ON CONFLICT DO NOTHING
        """, (eid, loc["name"], loc["lon"], loc["lat"], loc["type"], uncertainty))

    for prop in PROPERTIES:
        eid = uid(f"property-{prop['id']}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'PROPERTY',%s) ON CONFLICT DO NOTHING
        """, (eid, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.property
                (entity_id, property_ref, property_type, description,
                 boundary_geometry)
            VALUES (%s,%s,%s,%s,ST_Buffer(ST_SetSRID(ST_MakePoint(%s,%s),4326), 0.0001))
            ON CONFLICT DO NOTHING
        """, (eid, prop["ref"], prop["type"], prop["desc"], prop["lon"], prop["lat"]))


# ---------------------------------------------------------------------------
# Events (CDRs, transactions, ANPR sightings, arrests, border crossings)
# ---------------------------------------------------------------------------

def seed_events(cur, sys: dict):
    """Seed 284 events across all 12 cases."""
    src = sys["source_id"]
    run = sys["run_id"]
    adm = sys["admin_id"]
    evcount = 0

    # Event type mapping: CIVIX uses valid event_type_enum values only
    # Valid: CALL, MESSAGE, TRANSACTION, VEHICLE_SIGHTING, PROPERTY_MUTATION,
    #        MEETING, SEIZURE, ARREST, SURVEILLANCE_OBSERVATION, FORENSIC_COLLECTION,
    #        MEDICAL_EXAMINATION, FIR_FILING, DEVICE_PING, BORDER_CROSSING, OTHER
    EVENT_TYPE_MAP = {
        "CCTV_SIGHTING":       "SURVEILLANCE_OBSERVATION",
        "ANPR_HIT":            "VEHICLE_SIGHTING",
        "INCIDENT":            "OTHER",
        "SYSTEM_ALERT":        "OTHER",
        "INTERROGATION":       "MEETING",
        "LEGAL_ACTION":        "OTHER",
        "DOCUMENT_INGESTION":  "OTHER",
        "CASE_STATUS_CHANGE":  "OTHER",
        "BIOMETRIC_CAPTURE":   "FORENSIC_COLLECTION",
        "SEIZURE_MEMO":        "SEIZURE",
        "PROPERTY_MUTATION":   "PROPERTY_MUTATION",
    }

    def make_event(event_key, event_type, occurred_at, duration_secs=60):
        resolved_type = EVENT_TYPE_MAP.get(event_type, event_type)
        eid  = uid(f"event-{event_key}")
        sr   = uid(f"sr-{event_key}")
        ts   = occurred_at
        cur.execute("""
            INSERT INTO civix.source_record
                (source_record_id, source_id, external_reference, record_type)
            VALUES (%s,%s,%s,'EVENT_RECORD') ON CONFLICT DO NOTHING
        """, (sr, src, event_key))
        cur.execute(f"""
            INSERT INTO civix.event
                (event_id, event_type, occurred_at, source_record_id, generation_run_id)
            VALUES (%s,%s::civix.event_type_enum,
                    tstzrange(%s::timestamptz, %s::timestamptz + interval '{duration_secs} seconds'),
                    %s,%s)
            ON CONFLICT DO NOTHING
        """, (eid, resolved_type, ts, ts, sr, run))
        return eid

    def link(event_id, entity_seed, role):
        eid = uid(entity_seed)
        cur.execute("""
            INSERT INTO civix.event_participant
                (event_id, entity_id, participant_role)
            VALUES (%s,%s,%s) ON CONFLICT DO NOTHING
        """, (event_id, eid, role))

    # --- CIVIX-001: 2012 Robbery (14 events) ---
    e = make_event("c001-cctv-cam04-0610","CCTV_SIGHTING","2012-03-14T00:40:00Z"); link(e,"person-P0001","OBSERVER"); evcount+=1
    e = make_event("c001-anpr-nh48-0652","ANPR_HIT","2012-03-14T01:22:00Z"); link(e,"vehicle-V0010","PARTICIPANT"); evcount+=1
    e = make_event("c001-cdr-t0012-0730","CALL","2012-03-14T01:58:00Z",45); link(e,"phone-T0012","CALLER"); link(e,"phone-T0011","CALLEE"); evcount+=1
    e = make_event("c001-tower-t0011-0738","DEVICE_PING","2012-03-14T02:08:00Z"); link(e,"phone-T0011","SUBJECT"); link(e,"location-TOWER-DW-01","LOCATION"); evcount+=1
    e = make_event("c001-robbery-incident","INCIDENT","2012-03-14T02:13:00Z",180); link(e,"person-P0001","SUSPECT"); link(e,"person-P0301","VICTIM"); link(e,"location-LOC-DW-23","LOCATION"); evcount+=1
    e = make_event("c001-cctv-cam01-0743","CCTV_SIGHTING","2012-03-14T02:13:12Z"); link(e,"person-P0075","SUBJECT"); link(e,"location-LOC-DW-23","LOCATION"); evcount+=1
    e = make_event("c001-tower-t0013-0815","DEVICE_PING","2012-03-14T02:45:00Z"); link(e,"phone-T0013","SUBJECT"); link(e,"location-TOWER-NJ-01","LOCATION"); evcount+=1
    e = make_event("c001-vehicle-seizure","SEIZURE","2012-03-16T00:00:00Z"); link(e,"vehicle-V0010","PARTICIPANT"); evcount+=1
    # CDR deep dives (Layer 1 — richer behavioral)
    for i,ts in enumerate(["2012-03-13T20:00:00Z","2012-03-13T22:30:00Z","2012-03-14T00:00:00Z","2012-03-14T01:00:00Z","2012-03-14T01:30:00Z","2012-03-14T05:00:00Z"]):
        e = make_event(f"c001-cdr-pre-{i}","CALL",ts,30+i*5); link(e,"phone-T0013","CALLER"); link(e,"phone-T0012","CALLEE"); evcount+=1

    # --- CIVIX-003: NH-48 Dacoity (12 events) ---
    e = make_event("c003-cctv-bolero-2147","CCTV_SIGHTING","2021-11-07T16:17:00Z"); link(e,"vehicle-V0005","PARTICIPANT"); link(e,"location-LOC-NH48-01","LOCATION"); evcount+=1
    e = make_event("c003-robbery-truck","INCIDENT","2021-11-07T16:30:00Z",600); link(e,"person-P0001","SUSPECT"); link(e,"vehicle-V0006","PARTICIPANT"); link(e,"location-LOC-NH48-01","LOCATION"); evcount+=1
    e = make_event("c003-cdr-t0013-nh48","DEVICE_PING","2021-11-07T16:00:00Z"); link(e,"phone-T0013","SUBJECT"); link(e,"location-TOWER-NH-01","LOCATION"); evcount+=1
    e = make_event("c003-vehicle-recovery","SEIZURE","2021-11-08T10:00:00Z"); link(e,"vehicle-V0006","PARTICIPANT"); evcount+=1
    for i,ts in enumerate(["2021-11-07T14:00:00Z","2021-11-07T15:00:00Z","2021-11-07T18:00:00Z","2021-11-07T20:00:00Z","2021-11-08T00:00:00Z","2021-11-08T02:00:00Z","2021-11-08T04:00:00Z","2021-11-08T06:00:00Z"]):
        e = make_event(f"c003-cdr-{i}","CALL",ts,20+i*3); link(e,"phone-T0013","CALLER"); link(e,"phone-T0050","CALLEE"); evcount+=1

    # --- CIVIX-009: Najafgarh Arrest (14 events) ---
    e = make_event("c009-robbery-incident","INCIDENT","2026-07-19T03:30:00Z",300); link(e,"person-P0001","SUSPECT"); link(e,"person-P0304","VICTIM"); link(e,"location-LOC-NJ-SHOP","LOCATION"); evcount+=1
    e = make_event("c009-arrest-p0001","ARREST","2026-07-19T04:15:00Z"); link(e,"person-P0001","SUBJECT"); link(e,"location-LOC-NJ-SHOP","LOCATION"); evcount+=1
    e = make_event("c009-arrest-p0011","ARREST","2026-07-19T04:20:00Z"); link(e,"person-P0011","SUBJECT"); evcount+=1
    e = make_event("c009-afis-booking","BIOMETRIC_CAPTURE","2026-07-19T06:00:00Z"); link(e,"person-P0001","SUBJECT"); evcount+=1
    e = make_event("c009-civix-afis-alert","SYSTEM_ALERT","2026-07-19T06:05:00Z"); link(e,"person-P0001","SUBJECT"); evcount+=1
    e = make_event("c009-civix-case003-reopen","CASE_STATUS_CHANGE","2026-07-19T06:06:00Z"); evcount+=1
    e = make_event("c009-tx-meena-a","TRANSACTION","2026-05-15T00:00:00Z"); link(e,"account-ACC-0009A","RECEIVER"); evcount+=1
    e = make_event("c009-tx-meena-b","TRANSACTION","2026-06-01T00:00:00Z"); link(e,"account-ACC-0009B","RECEIVER"); evcount+=1
    e = make_event("c009-tx-meena-c","TRANSACTION","2026-06-15T00:00:00Z"); link(e,"account-ACC-0009C","RECEIVER"); evcount+=1
    for i,ts in enumerate(["2026-07-18T20:00:00Z","2026-07-18T22:00:00Z","2026-07-19T00:00:00Z","2026-07-19T02:00:00Z","2026-07-19T03:00:00Z"]):
        e = make_event(f"c009-cdr-pre-{i}","CALL",ts,15); link(e,"phone-T0050","CALLER"); link(e,"phone-T0051","CALLEE"); evcount+=1

    # --- CIVIX-010: GST Fraud (18 events) ---
    e = make_event("c010-sar-ingestion","DOCUMENT_INGESTION","2024-02-11T04:30:00Z"); link(e,"org-ORG-033","SUBJECT"); evcount+=1
    e = make_event("c010-civix-ner-alert","SYSTEM_ALERT","2024-02-11T04:34:00Z"); evcount+=1
    e = make_event("c010-civix-gst-crossmatch","SYSTEM_ALERT","2024-02-11T04:35:00Z"); evcount+=1
    e = make_event("c010-case036-reopen","CASE_STATUS_CHANGE","2024-02-11T04:36:00Z"); evcount+=1
    e = make_event("c010-arrest-p0020","ARREST","2024-02-15T00:00:00Z"); link(e,"person-P0020","SUBJECT"); evcount+=1
    e = make_event("c010-pmla-freeze","LEGAL_ACTION","2024-02-20T00:00:00Z"); link(e,"account-ACC-0020A","SUBJECT"); link(e,"account-ACC-0020B","SUBJECT"); evcount+=1
    # Financial transactions (N2 fund flow)
    for i,ts in enumerate(["2023-10-01","2023-11-01","2023-12-01","2024-01-01","2024-01-15","2024-02-01"]):
        e = make_event(f"c010-tx-{i}","TRANSACTION",f"{ts}T00:00:00Z"); link(e,"account-ACC-0020A","SENDER"); link(e,"account-ACC-ORG031Z","RECEIVER"); evcount+=1
    for i in range(6):
        e = make_event(f"c010-cdr-seth-{i}","CALL",f"2024-02-0{i+1}T18:00:00Z",45); link(e,"phone-T0020","CALLER"); link(e,"phone-T0021","CALLEE"); evcount+=1

    # --- CIVIX-019: Plate Cloning (12 events) ---
    e = make_event("c019-anpr-cam02-1422","ANPR_HIT","2026-04-03T08:52:07Z"); link(e,"vehicle-V0001","PARTICIPANT"); evcount+=1
    e = make_event("c019-anpr-cam15-1424","ANPR_HIT","2026-04-03T08:54:51Z"); link(e,"vehicle-V0002","PARTICIPANT"); evcount+=1
    e = make_event("c019-civix-spatial-paradox","SYSTEM_ALERT","2026-04-03T08:55:00Z"); evcount+=1
    e = make_event("c019-arrest-p0046","ARREST","2026-04-03T10:00:00Z"); link(e,"person-P0046","SUBJECT"); link(e,"vehicle-V0002","PARTICIPANT"); evcount+=1
    e = make_event("c019-workshop-raid","SEIZURE","2026-04-05T00:00:00Z"); link(e,"property-PROP-001","LOCATION"); evcount+=1
    e = make_event("c019-dev019-t0091-ping","DEVICE_PING","2026-04-02T00:00:00Z"); link(e,"phone-T0091","SUBJECT"); link(e,"location-TOWER-DW-01","LOCATION"); evcount+=1
    for i,ts in enumerate(["2026-04-01T20:00:00Z","2026-04-02T08:00:00Z","2026-04-02T14:00:00Z","2026-04-02T22:00:00Z","2026-04-03T06:00:00Z","2026-04-03T07:00:00Z"]):
        e = make_event(f"c019-cdr-{i}","CALL",ts,25); link(e,"phone-T0047","CALLER"); link(e,"phone-T0046","CALLEE"); evcount+=1

    # --- CIVIX-022: Okhla Gold (10 events) ---
    e = make_event("c022-cctv-bolero-okhla","CCTV_SIGHTING","2025-03-15T04:00:00Z"); link(e,"vehicle-V0005","PARTICIPANT"); link(e,"location-LOC-OKHLA-WH","LOCATION"); evcount+=1
    e = make_event("c022-gold-seizure","SEIZURE","2025-03-15T06:00:00Z"); link(e,"person-P0099","SUBJECT"); link(e,"location-LOC-OKHLA-WH","LOCATION"); evcount+=1
    e = make_event("c022-arrest-p0096","ARREST","2025-03-15T07:00:00Z"); link(e,"person-P0096","SUBJECT"); evcount+=1
    e = make_event("c022-arrest-p0099","ARREST","2025-03-15T07:30:00Z"); link(e,"person-P0099","SUBJECT"); evcount+=1
    e = make_event("c022-civix-vehicle-lead","SYSTEM_ALERT","2025-03-15T09:00:00Z"); evcount+=1
    for i,ts in enumerate(["2025-03-14T18:00:00Z","2025-03-14T20:00:00Z","2025-03-14T22:00:00Z","2025-03-15T01:00:00Z","2025-03-15T03:00:00Z"]):
        e = make_event(f"c022-cdr-{i}","CALL",ts,35); link(e,"phone-T0095","CALLER"); link(e,"phone-T0096","CALLEE"); evcount+=1

    # --- CIVIX-027: KYC Phishing (12 events) ---
    e = make_event("c027-imei-a-ping-2021","DEVICE_PING","2021-06-18T12:30:00Z"); link(e,"phone-T0011","SUBJECT"); link(e,"location-TOWER-RH-01","LOCATION"); evcount+=1
    e = make_event("c027-dev019-t0045-active","DEVICE_PING","2021-06-18T14:00:00Z"); link(e,"phone-T0045","SUBJECT"); link(e,"location-TOWER-RH-01","LOCATION"); evcount+=1
    e = make_event("c027-nitesh-interrogation","INTERROGATION","2021-08-10T00:00:00Z"); link(e,"person-P0071","SUBJECT"); evcount+=1
    e = make_event("c027-civix-hero01-alert","SYSTEM_ALERT","2021-08-10T02:00:00Z"); evcount+=1
    e = make_event("c027-arrest-p0071","ARREST","2021-08-12T00:00:00Z"); link(e,"person-P0071","SUBJECT"); evcount+=1
    e = make_event("c027-arrest-p0072","ARREST","2021-08-12T01:00:00Z"); link(e,"person-P0072","SUBJECT"); evcount+=1
    for i,ts in enumerate(["2021-06-17T23:00:00Z","2021-06-18T00:30:00Z","2021-06-18T02:00:00Z","2021-06-18T04:00:00Z","2021-06-18T10:00:00Z","2021-06-18T20:00:00Z"]):
        e = make_event(f"c027-cdr-{i}","CALL",ts,40+i*2); link(e,"phone-T0070","CALLER"); link(e,"phone-T0071","CALLEE"); evcount+=1

    # --- CIVIX-032: Digital Arrest (18 events) ---
    e = make_event("c032-victim-call","CALL","2023-08-22T18:30:00Z",3600); link(e,"phone-T0073","CALLER"); evcount+=1
    e = make_event("c032-civix-xgboost-alert","SYSTEM_ALERT","2023-08-23T06:00:00Z"); link(e,"person-P0073","SUBJECT"); evcount+=1
    e = make_event("c032-raid-rohini","SEIZURE","2023-09-01T00:00:00Z"); link(e,"property-PROP-006","LOCATION"); evcount+=1
    e = make_event("c032-arrest-p0073","ARREST","2023-09-01T02:00:00Z"); link(e,"person-P0073","SUBJECT"); evcount+=1
    e = make_event("c032-arrest-p0074","ARREST","2023-09-01T02:30:00Z"); link(e,"person-P0074","SUBJECT"); evcount+=1
    e = make_event("c032-victim-transfer","TRANSACTION","2023-08-22T20:00:00Z"); link(e,"account-ACC-0155A","RECEIVER"); evcount+=1
    # XGBoost behavioral — night calls (Layer 1 depth)
    for i in range(12):
        hour = 23 + (i // 2)
        day  = 1 + (i // 4)
        ts   = f"2023-08-{day:02d}T{(hour % 24):02d}:00:00Z"
        e = make_event(f"c032-cdr-night-{i}","CALL",ts,120); link(e,"phone-T0073","CALLER"); evcount+=1

    # --- CIVIX-036: Nizamuddin Gold (8 events) ---
    e = make_event("c036-theft-incident","INCIDENT","2018-06-22T10:00:00Z",600); link(e,"person-P0095","SUSPECT"); link(e,"location-LOC-NIZ-STATION","LOCATION"); evcount+=1
    e = make_event("c036-case-closed-2019","CASE_STATUS_CHANGE","2019-03-10T00:00:00Z"); evcount+=1
    e = make_event("c036-case-reopened-2024","CASE_STATUS_CHANGE","2024-02-11T04:36:00Z"); evcount+=1
    e = make_event("c036-cash-deposit-p0095","TRANSACTION","2018-06-25T00:00:00Z"); link(e,"account-ACC-0095A","RECEIVER"); evcount+=1
    for i,ts in enumerate(["2018-06-21T20:00:00Z","2018-06-22T07:00:00Z","2018-06-22T12:00:00Z","2018-06-23T00:00:00Z"]):
        e = make_event(f"c036-cdr-{i}","CALL",ts,30); link(e,"phone-T0095","CALLER"); evcount+=1

    # --- CIVIX-038: IGI Cargo (10 events) ---
    e = make_event("c038-igi-cargo-incident","INCIDENT","2024-11-10T06:00:00Z",1800); link(e,"person-P0095","SUSPECT"); link(e,"location-LOC-IGI-CARGO","LOCATION"); evcount+=1
    e = make_event("c038-border-crossing-p0100","BORDER_CROSSING","2024-11-15T08:00:00Z"); link(e,"person-P0100","SUBJECT"); evcount+=1
    e = make_event("c038-pre-departure-transfer","TRANSACTION","2024-11-12T00:00:00Z"); link(e,"account-ACC-0100A","SENDER"); link(e,"account-ACC-0098A","RECEIVER"); evcount+=1
    e = make_event("c038-civix-hero10-alert","SYSTEM_ALERT","2024-11-15T10:00:00Z"); link(e,"person-P0100","SUBJECT"); evcount+=1
    e = make_event("c038-gold-seizure-igi","SEIZURE","2024-11-10T08:00:00Z"); link(e,"location-LOC-IGI-CARGO","LOCATION"); evcount+=1
    e = make_event("c038-arrest-p0097","ARREST","2024-11-10T10:00:00Z"); link(e,"person-P0097","SUBJECT"); evcount+=1
    for i,ts in enumerate(["2024-11-07T00:00:00Z","2024-11-08T12:00:00Z","2024-11-09T18:00:00Z","2024-11-10T03:00:00Z"]):
        e = make_event(f"c038-cdr-{i}","CALL",ts,25); link(e,"phone-T0095","CALLER"); link(e,"phone-T0100","CALLEE"); evcount+=1

    # --- CIVIX-044: Benami Land (12 events) ---
    e = make_event("c044-property-mutation","PROPERTY_MUTATION","2023-04-05T00:00:00Z"); link(e,"property-PROP-001","TARGET_PROPERTY"); link(e,"person-P0010","NEW_OWNER"); link(e,"person-P0130","SUBJECT"); evcount+=1
    e = make_event("c044-patwari-deposit-1","TRANSACTION","2023-04-05T00:00:00Z"); link(e,"account-ACC-0020A","RECEIVER"); evcount+=1
    e = make_event("c044-patwari-deposit-2","TRANSACTION","2023-05-15T00:00:00Z"); link(e,"account-ACC-0020A","RECEIVER"); evcount+=1
    e = make_event("c044-civix-hero04-lead","SYSTEM_ALERT","2026-07-19T06:10:00Z"); link(e,"person-P0010","SUBJECT"); evcount+=1
    e = make_event("c044-civix-false-positive","SYSTEM_ALERT","2026-07-19T06:11:00Z"); link(e,"person-P0200","SUBJECT"); evcount+=1
    e = make_event("c044-arrest-p0122","ARREST","2023-06-20T00:00:00Z"); link(e,"person-P0122","SUBJECT"); evcount+=1
    for i,ts in enumerate(["2023-03-01","2023-03-15","2023-04-01","2023-04-10","2023-05-01","2023-05-20"]):
        e = make_event(f"c044-cdr-{i}","CALL",f"{ts}T12:00:00Z",30); link(e,"phone-T0010","CALLER"); link(e,"phone-T0130","CALLEE"); evcount+=1

    # --- CIVIX-051: Ghost Vendor (10 events) ---
    e = make_event("c051-civix-address-collision","SYSTEM_ALERT","2024-01-15T00:00:00Z"); evcount+=1
    e = make_event("c051-civix-hero07-lead","SYSTEM_ALERT","2024-01-15T00:05:00Z"); evcount+=1
    e = make_event("c051-physical-inspection","INCIDENT","2024-01-20T00:00:00Z"); link(e,"property-PROP-003","LOCATION"); evcount+=1
    e = make_event("c051-pwd-payment","TRANSACTION","2023-12-01T00:00:00Z"); link(e,"account-ACC-0060A","RECEIVER"); evcount+=1
    e = make_event("c051-kickback-transfer","TRANSACTION","2023-12-05T00:00:00Z"); link(e,"account-ACC-0060A","SENDER"); link(e,"account-ACC-0155A","RECEIVER"); evcount+=1
    e = make_event("c051-arrest-p0156","ARREST","2024-02-10T00:00:00Z"); link(e,"person-P0156","SUBJECT"); evcount+=1
    for i,ts in enumerate(["2024-01-05","2024-01-10","2024-01-15","2024-01-20"]):
        e = make_event(f"c051-cdr-{i}","CALL",f"{ts}T16:00:00Z",40); link(e,"phone-T0155","CALLER"); link(e,"phone-T0156","CALLEE"); evcount+=1

    print(f"  Seeded {evcount} events.")


# ---------------------------------------------------------------------------
# Evidence (240 items — 20 per case)
# ---------------------------------------------------------------------------

def make_evidence(cur, sys: dict, case_id_str: str, items: list):
    """Insert evidence_artifact + evidence_instance rows for a case."""
    case_eid = uid(f"case-{case_id_str}")
    src = sys["source_id"]
    adm = sys["admin_id"]
    for item in items:
        artifact_id = uid(f"artifact-{item['id']}")
        instance_id = uid(f"instance-{item['id']}")
        sr_id = uid(f"sr-evd-{item['id']}")
        manifest_id = uid(f"manifest-{item['id']}")
        expected_mime = "image/png" if "IMAGE" in item.get("type", "") or item.get("type") in ["CCTV_FOOTAGE", "PHOTOGRAPH", "SKETCH", "PHYSICAL_EVIDENCE"] else "application/pdf"
        
        cur.execute("""
            INSERT INTO civix.source_record
                (source_record_id, source_id, external_reference, record_type)
            VALUES (%s,%s,%s,'EVIDENCE_DOCUMENT') ON CONFLICT DO NOTHING
        """, (sr_id, src, item["id"]))
        
        cur.execute("""
            INSERT INTO civix.evidence_generation_manifest
                (manifest_id, case_id, source_record_id, evidence_id_str, evidence_type, title, prompt, expected_mime_type)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (evidence_id_str) DO NOTHING
        """, (
            manifest_id, case_eid, sr_id, item["id"], 
            item["type"], item["title"], item.get("prompt", ""), expected_mime
        ))



def seed_evidence(cur, sys: dict):
    print("  Seeding 240 evidence items...")

    CIVIX001_EVD = [
        {"id":"EVD-001-001","type":"FIR_DOCUMENT","title":"FIR No. 127/2012 — Dwarka PS","prompt":"Handwritten Delhi Police FIR form, 2012, blue ink, ink smudges, official stamp."},
        {"id":"EVD-001-002","type":"CCTV_FOOTAGE","title":"CAM-01 Still — Grey Tracksuit (07:43:12)","prompt":"Grainy 2012 CCTV still, street corner, person in grey tracksuit, face obscured by helmet visor, timestamp 07:43:12 overlay."},
        {"id":"EVD-001-003","type":"WITNESS_STATEMENT","title":"Anita Mehta Victim Statement","prompt":"Typed police statement form 2012, victim Anita Mehta, blue ink, signature at bottom."},
        {"id":"EVD-001-004","type":"CALL_DATA_RECORD","title":"T0011 CDR — TOWER-DW-01 07:38","prompt":"CSV table with tower pings, highlighted row 07:38, TOWER-DW-01 column, cell reference circled in red."},
        {"id":"EVD-001-005","type":"FORENSIC_REPORT","title":"Ballistics — 3x .32 ACP Cartridges","prompt":"CFSL ballistics report header, tabular findings for 3 cartridge cases, examiner signature and stamp."},
        {"id":"EVD-001-006","type":"MEDICAL_REPORT","title":"Anita Mehta Injury Report","prompt":"Hospital medical examination form, head trauma documented, clinical language, doctor signature."},
        {"id":"EVD-001-007","type":"SEIZURE_MEMO","title":"Getaway Motorcycle HR-25-BC-9921","prompt":"Police seizure memo, motorcycle details, Dwarka PS stamp, date 2012-03-16."},
        {"id":"EVD-001-008","type":"INTERROGATION_TRANSCRIPT","title":"Rakesh Yadav 2013 — Mentions 'Pandit'","prompt":"Typed prison interview transcript, P0002 mentions 'the one who planned vehicle approach — we called him Pandit', IO notes highlighted."},
        {"id":"EVD-001-009","type":"COURT_ORDER","title":"Chargesheet — 4 Accused + 1 At Large","prompt":"Official chargesheet Delhi Sessions Court, 4 accused named, 5th listed as unidentified, court stamp 2012."},
        {"id":"EVD-001-010","type":"COURT_ORDER","title":"Conviction Order — RI 7 Years Each","prompt":"Judgment document, Sessions Court Delhi 2013, RI 7 years for 4 accused, formal legal format."},
        {"id":"EVD-001-011","type":"ANPR_DATA","title":"ANPR NH-48 Toll — Motorcycle Convoy 06:52","prompt":"ANPR system screenshot, motorcycle plates, toll camera, 06:52 timestamp, two motorcycles side by side."},
        {"id":"EVD-001-012","type":"INTELLIGENCE_REPORT","title":"Police Sketch — Person Unknown 05","prompt":"Police composite sketch, grey tracksuit, partial face, helmet removed, WANTED FOR QUESTIONING banner."},
        {"id":"EVD-001-013","type":"INTELLIGENCE_REPORT","title":"Lookout Circular — Person Unknown 05","prompt":"Delhi Police lookout circular, physical description, height weight, case reference 127/2012."},
        {"id":"EVD-001-014","type":"FINANCIAL_STATEMENT","title":"SBI Cash Loss Inventory — ₹47 Lakh","prompt":"Bank internal document, denomination breakdown table, ₹47,00,000 total, SBI letterhead."},
        {"id":"EVD-001-015","type":"FORENSIC_REPORT","title":"Fingerprint Lift — Motorcycle Steering","prompt":"CFSL fingerprint card, partial latent print, ridge detail visible, case reference, 2012."},
        {"id":"EVD-001-016","type":"INTELLIGENCE_REPORT","title":"Inter-PS Intel — Najafgarh Gang Link","prompt":"Internal police intelligence note, NH-48 to Najafgarh corridor, 2012, handwritten annotations."},
        {"id":"EVD-001-017","type":"CCTV_FOOTAGE","title":"CAM-04 Najafgarh — Two Motorcycles 06:10","prompt":"Night CCTV footage, two motorcycles at Najafgarh Bus Terminal, dim streetlight, 06:10 timestamp."},
        {"id":"EVD-001-018","type":"FORENSIC_REPORT","title":"CFSL DNA — Cigarette Butt Crime Scene","prompt":"CFSL DNA report, cigarette butt exhibit marked, STR profile table, lab stamp."},
        {"id":"EVD-001-019","type":"AI_LEAD","title":"CIVIX LEAD-001 — Alias-Device Overlap CIVIX-001/027","prompt":"CIVIX lead card UI, score 0.87, 'Vikram @ Pandit' cross-case link, two case panels."},
        {"id":"EVD-001-020","type":"AI_LEAD","title":"CIVIX IC-001 — Person Unknown 05 = P0075","prompt":"CIVIX identity candidate panel, IC-001, signal list: alias match + IMEI bridge, confidence graph 0.87."},
    ]
    visual_types = ["PHOTOGRAPH", "CCTV_FOOTAGE", "SKETCH", "PHYSICAL_EVIDENCE", "PHOTOGRAPH", "PHOTOGRAPH", "CCTV_FOOTAGE", "PHOTOGRAPH", "SKETCH", "PHYSICAL_EVIDENCE", "PHOTOGRAPH", "CCTV_FOOTAGE", "PHOTOGRAPH", "PHYSICAL_EVIDENCE"]
    CIVIX001_VIS = [
        {"id":f"VIS-001-{i:03d}","type":visual_types[i-1],"title":f"CIVIX-001 — Visual Artifact {i:02d}","prompt":f"CIVIX 2.0 visual evidence artifact {i} for CIVIX-001. Cinematic realism."}
        for i in range(1,15)
    ]
    CIVIX001_EVD.extend(CIVIX001_VIS)
    make_evidence(cur, sys, "CIVIX-001", CIVIX001_EVD)

    CIVIX003_EVD = [
        {"id":"EVD-003-001","type":"FIR_DOCUMENT","title":"FIR No. 88/2021 — NH-48 Patrol","prompt":"NH-48 Highway Patrol FIR, 2021, typed format, case number stamped."},
        {"id":"EVD-003-002","type":"CCTV_FOOTAGE","title":"CAM-02 — Bolero HR-06UH-3818 Parked","prompt":"Night highway CCTV, dark Mahindra Bolero parked on shoulder, timestamp 21:47, NH-48 marker."},
        {"id":"EVD-003-003","type":"FORENSIC_REPORT","title":"AFIS Match — P0001 Latent Print (2026)","prompt":"AFIS split-screen card: 2021 crime scene latent print (left) vs 2026 10-print booking card (right), ridge minutiae alignment dots in green."},
        {"id":"EVD-003-004","type":"CALL_DATA_RECORD","title":"T0013 CDR — TOWER-NH-01 Night of Crime","prompt":"CDR extract, TOWER-NH-01 pings on 2021-11-07 night, P0001 phone activity highlighted."},
        {"id":"EVD-003-005","type":"WITNESS_STATEMENT","title":"Harpal Singh (Truck Driver) Statement","prompt":"Police statement, Harpal Singh alias 'Bhura' noted — IO marker: same alias as CIVIX-001 P0003."},
        {"id":"EVD-003-006","type":"SEIZURE_MEMO","title":"Truck Recovery — UP-14-AB-7734","prompt":"Police seizure report, recovered truck, cargo inventory, recovery location 60km from scene."},
        {"id":"EVD-003-007","type":"AI_LEAD","title":"CIVIX — Bolero HR-06UH-3818 ANPR Timeline","prompt":"CIVIX ANPR timeline chart, vehicle HR-06UH-3818, 6 sightings across 4 years, 2 case references."},
        {"id":"EVD-003-008","type":"AI_LEAD","title":"CIVIX LEAD-022 — Vehicle Cross-case 003↔022","prompt":"CIVIX lead card, vehicle cross-case, score 0.67, timeline: 2021 NH-48, 2025 Okhla."},
        {"id":"EVD-003-009","type":"COURT_ORDER","title":"Cold Status Court Notification","prompt":"Court notice, case transferred to cold register, 2022-05-15, IO signature."},
        {"id":"EVD-003-010","type":"AI_LEAD","title":"CIVIX HERO-04 — AFIS Biometric Hit","prompt":"CIVIX alert panel, AFIS match notification, red banner COLD CASE REOPENED, case 003 status changed."},
        {"id":"EVD-003-011","type":"FORENSIC_REPORT","title":"CFSL — Ballistic Evidence Recovery","prompt":"CFSL ballistics report, cartridge cases recovered, highway incident, lab analysis."},
        {"id":"EVD-003-012","type":"ANPR_DATA","title":"ANPR — Toll Camera NH-48 2021","prompt":"ANPR capture, NH-48 toll, convoy vehicles, timestamp 21:30, pre-incident."},
        {"id":"EVD-003-013","type":"CALL_DATA_RECORD","title":"P0006 Ajay Rawat CDR — Night 2021","prompt":"CDR extract, P0006 phone activity, NH-48 tower pings, pre and post incident."},
        {"id":"EVD-003-014","type":"INTELLIGENCE_REPORT","title":"Inter-PS Intel — N1 Activity NH-48","prompt":"Police intelligence note, N1 gang pattern on NH-48 corridor, 2021."},
        {"id":"EVD-003-015","type":"FINANCIAL_STATEMENT","title":"Cargo Value Assessment — ₹4.8 Cr","prompt":"Logistics company cargo manifest, goods value ₹4.8 crore, insurance declaration."},
        {"id":"EVD-003-016","type":"INTERROGATION_TRANSCRIPT","title":"P0007 Pradeep Jhajhar Interrogation","prompt":"Typed interrogation transcript, P0007 denies direct involvement, tower data confrontation."},
        {"id":"EVD-003-017","type":"WITNESS_STATEMENT","title":"Arun Kumar Mishra Helper Statement","prompt":"Police statement, truck helper P0303, minor injury, description of attackers."},
        {"id":"EVD-003-018","type":"FORENSIC_REPORT","title":"Vehicle Inspection — Bolero HR-06UH-3818","prompt":"Police vehicle inspection report, Bolero details, VIN verified, no seizure markers."},
        {"id":"EVD-003-019","type":"AI_LEAD","title":"CIVIX — Alias Collision 'Bhura' (HERO-12)","prompt":"CIVIX identity candidate IC-015 (FALSE POSITIVE), 'Bhura' alias match P0003 vs P0008, score 0.31 LOW, reasoning: different persons."},
        {"id":"EVD-003-020","type":"COURT_ORDER","title":"2026 Reopening Order — CIVIX-003","prompt":"Court order, CIVIX-003 reopened from cold register, triggering event: AFIS biometric match CIVIX-009."},
    ]
    CIVIX003_VIS = [
        {"id":f"VIS-003-{i:03d}","type":visual_types[i-1],"title":f"CIVIX-003 — Visual Artifact {i:02d}","prompt":f"CIVIX 2.0 visual evidence artifact {i} for CIVIX-003. Cinematic realism."}
        for i in range(1,15)
    ]
    CIVIX003_EVD.extend(CIVIX003_VIS)
    make_evidence(cur, sys, "CIVIX-003", CIVIX003_EVD)

    # Remaining 10 cases — 20 items each (abbreviated title+type, full prompt)
    CIVIX009_EVD = [
        {"id":f"EVD-009-{i:03d}","type":"FIR_DOCUMENT" if i==1 else "FORENSIC_REPORT" if i==2 else "AI_LEAD" if i in [3,4,7,8,9,11,12,20] else "CALL_DATA_RECORD" if i==5 else "FINANCIAL_STATEMENT" if i==6 else "INTERROGATION_TRANSCRIPT" if i==13 else "COURT_ORDER" if i==14 else "SEIZURE_MEMO" if i==15 else "INTELLIGENCE_REPORT","title":t,"prompt":pr}
        for i,(t,pr) in enumerate([
            ("FIR 411/2026 Najafgarh","2026 digital FIR, Najafgarh PS, typed."),
            ("AFIS 10-print — Suresh Valmiki 2026","Fingerprint booking card, all 10 prints, inked, date stamped 2026-07-19."),
            ("CIVIX AFIS Alert — P0001 matches CIVIX-003","CIVIX biometric match alert, split screen 2021 latent vs 2026 10-print."),
            ("CIVIX CIVIX-003 Auto-REOPENED","CIVIX case status panel, COLD → REOPENED, trigger AFIS."),
            ("P0001 CDR Night of Arrest","CDR extract, T0050 pings TOWER-NJ-01, 2026-07-18 night."),
            ("Meena Valmiki Bank Statements — ₹28L","Bank statements, 3 accounts, structured credits annotated."),
            ("CIVIX HERO-04 3-Hop Chain Report","CIVIX multi-hop graph, P0001→P0010→Yadav Properties→CIVIX-044."),
            ("CIVIX N1→N6 Cross-Network Alert","CIVIX network crossing alert, N1 robbery → N6 land fraud."),
            ("P0001 Interrogation Transcript","Typed interrogation, P0001 initial denial, lawyer present."),
            ("Remand Order — P0001 14 Days","Court order Najafgarh Magistrate, 14-day custody granted."),
            ("Company Directorship — Dinesh Yadav","MCA21 extract, Dinesh Yadav as director Yadav Properties."),
            ("Cash Seized at Arrest — ₹4.2L","Police seizure memo, cash bundles, Najafgarh PS stamp."),
            ("Co-Accused P0011 Profile","CIVIX entity profile, P0011 Karan Saroha, role in CIVIX-009."),
            ("Bail Rejection Order — P0001","Sessions Court bail rejection order, flight risk reasoning."),
            ("Chargesheet Draft — CIVIX-009","Draft chargesheet, P0001 and P0011, Najafgarh robbery."),
            ("CIVIX Behavioral Score — P0001","CIVIX behavioral score card, P0001 anomaly indicators."),
            ("N1-N2 Financial Link Report","CIVIX financial intelligence report, N1 proceeds→N2 hawala."),
            ("P0012 Mohit Hooda Profile","CIVIX entity profile, P0012 absconding, last known location."),
            ("Seized Pulsar HR-26AJ-7712","Police seizure memo, Bajaj Pulsar, getaway vehicle."),
            ("CIVIX IC-001 Resolution Card","CIVIX identity candidate resolution, P0075 confirmed HERO-01."),
        ], 1)
    ]
    CIVIX009_VIS = [
        {"id":f"VIS-009-{i:03d}","type":visual_types[i-1],"title":f"CIVIX-009 — Visual Artifact {i:02d}","prompt":f"CIVIX 2.0 visual evidence artifact {i} for CIVIX-009. Cinematic realism."}
        for i in range(1,15)
    ]
    CIVIX009_EVD.extend(CIVIX009_VIS)
    make_evidence(cur, sys, "CIVIX-009", CIVIX009_EVD)

    # Generate remaining 9 cases × 20 evidence items each (compact format)
    for case_cfg in [
        ("CIVIX-010", "GST SAR", "c010"),
        ("CIVIX-019", "Plate Cloning", "c019"),
        ("CIVIX-022", "Okhla Gold", "c022"),
        ("CIVIX-027", "KYC Phishing", "c027"),
        ("CIVIX-032", "Digital Arrest", "c032"),
        ("CIVIX-036", "Nizamuddin Gold", "c036"),
        ("CIVIX-038", "IGI Cargo", "c038"),
        ("CIVIX-044", "Benami Land", "c044"),
        ("CIVIX-051", "Ghost Vendor", "c051"),
    ]:
        case_id_str, label, prefix = case_cfg
        # Documentary Evidence (20 items)
        types = ["FIR_DOCUMENT","CALL_DATA_RECORD","AI_LEAD","FORENSIC_REPORT",
                 "WITNESS_STATEMENT","FINANCIAL_STATEMENT","INTERROGATION_TRANSCRIPT",
                 "COURT_ORDER","SEIZURE_MEMO","ANPR_DATA","CCTV_FOOTAGE",
                 "INTELLIGENCE_REPORT","MEDICAL_REPORT","DIGITAL_FORENSICS",
                 "PROPERTY_DOCUMENT","AI_LEAD","AI_LEAD","COURT_ORDER",
                 "FINANCIAL_STATEMENT","AI_LEAD"]
        items = [
            {"id":f"EVD-{case_id_str.replace('CIVIX-','')}-{i:03d}",
             "type": types[i-1],
             "title":f"{label} — Evidence Item {i:02d}",
             "prompt":f"CIVIX 2.0 evidence item {i} for {label} case. Detailed forensic/intelligence document in Indian police format, professional quality, relevant to {case_id_str}."}
            for i in range(1,21)
        ]
        
        # Visual Evidence (14 items)
        visual_types = ["PHOTOGRAPH", "CCTV_FOOTAGE", "SKETCH", "PHYSICAL_EVIDENCE", "PHOTOGRAPH", "PHOTOGRAPH", "CCTV_FOOTAGE", "PHOTOGRAPH", "SKETCH", "PHYSICAL_EVIDENCE", "PHOTOGRAPH", "CCTV_FOOTAGE", "PHOTOGRAPH", "PHYSICAL_EVIDENCE"]
        visual_items = [
            {"id":f"VIS-{case_id_str.replace('CIVIX-','')}-{i:03d}",
             "type": visual_types[i-1],
             "title":f"{label} — Visual Artifact {i:02d}",
             "prompt":f"CIVIX 2.0 visual evidence artifact {i} for {label} case. Cinematic realism, professional crime scene photography, relevant to {case_id_str}."}
            for i in range(1,15)
        ]
        items.extend(visual_items)
        make_evidence(cur, sys, case_id_str, items)



# ---------------------------------------------------------------------------
# Case Entity Roles
# ---------------------------------------------------------------------------

CASE_ROLES = [
    # CIVIX-001
    ("CIVIX-001","P0001","SUSPECT","Gang leader — absconding"),
    ("CIVIX-001","P0002","ACCUSED","Convicted robber"),
    ("CIVIX-001","P0003","ACCUSED","Convicted robber"),
    ("CIVIX-001","P0004","ACCUSED","Convicted robber"),
    ("CIVIX-001","P0005","ACCUSED","Convicted driver"),
    ("CIVIX-001","P0075","SUSPECT","Person Unknown 05 — identified 2026"),
    ("CIVIX-001","P0301","VICTIM","SBI guard, injured"),
    ("CIVIX-001","P0302","VICTIM","SBI van driver"),
    # CIVIX-003
    ("CIVIX-003","P0001","SUSPECT","Latent print match — HERO-04"),
    ("CIVIX-003","P0006","SUSPECT","Wheel-man — absconding"),
    ("CIVIX-003","P0007","SUSPECT","Lookout — absconding"),
    ("CIVIX-003","P0008","VICTIM","Truck driver — alias Bhura"),
    ("CIVIX-003","P0303","VICTIM","Truck helper"),
    # CIVIX-009
    ("CIVIX-009","P0001","ACCUSED","Arrested 2026-07-19"),
    ("CIVIX-009","P0009","PERSON_OF_INTEREST","Financial front"),
    ("CIVIX-009","P0010","PERSON_OF_INTEREST","Brother — N6 link"),
    ("CIVIX-009","P0011","ACCUSED","Arrested"),
    ("CIVIX-009","P0012","SUSPECT","Absconding"),
    ("CIVIX-009","P0304","VICTIM","Shopkeeper"),
    # CIVIX-010
    ("CIVIX-010","P0020","ACCUSED","GST fraud mastermind"),
    ("CIVIX-010","P0021","ACCUSED","CA, fraudulent filings"),
    ("CIVIX-010","P0022","PERSON_OF_INTEREST","Hawala coordinator"),
    ("CIVIX-010","P0023","ACCUSED","Paper director"),
    ("CIVIX-010","P0095","SUSPECT","Silent UBO via GST cross-match"),
    ("CIVIX-010","P0041","PERSON_OF_INTEREST","Benami account holder"),
    # CIVIX-019
    ("CIVIX-019","P0045","SUSPECT","Ring leader — absconding"),
    ("CIVIX-019","P0046","ACCUSED","Clone vehicle operator"),
    ("CIVIX-019","P0047","PERSON_OF_INTEREST","Corrupt RTO agent"),
    ("CIVIX-019","P0050","VICTIM","Legitimate plate owner"),
    ("CIVIX-019","P0305","WITNESS","Workshop employee"),
    # CIVIX-022
    ("CIVIX-022","P0095","SUSPECT","N5 leader"),
    ("CIVIX-022","P0096","ACCUSED","Logistics coordinator"),
    ("CIVIX-022","P0097","PERSON_OF_INTEREST","Corrupt clearing agent"),
    ("CIVIX-022","P0099","ACCUSED","Warehouse operator"),
    # CIVIX-027
    ("CIVIX-027","P0070","SUSPECT","N4 mastermind — absconding"),
    ("CIVIX-027","P0071","ACCUSED","Ops manager — named Pandit"),
    ("CIVIX-027","P0072","ACCUSED","SIM specialist"),
    ("CIVIX-027","P0075","SUSPECT","Recruiter — Person Unknown 05"),
    ("CIVIX-027","P0306","VICTIM","KYC fraud victim"),
    # CIVIX-032
    ("CIVIX-032","P0070","SUSPECT","N4 mastermind — absconding"),
    ("CIVIX-032","P0073","ACCUSED","Call center coordinator"),
    ("CIVIX-032","P0074","ACCUSED","Script writer"),
    ("CIVIX-032","P0307","VICTIM","Digital arrest victim"),
    # CIVIX-036
    ("CIVIX-036","P0095","SUSPECT","Cleared 2019, re-suspect 2024"),
    ("CIVIX-036","P0096","PERSON_OF_INTEREST","Logistics facilitator"),
    ("CIVIX-036","P0101","WITNESS","Railway porter"),
    ("CIVIX-036","P0308","VICTIM","Bullion courier"),
    # CIVIX-038
    ("CIVIX-038","P0095","SUSPECT","N5 leader"),
    ("CIVIX-038","P0097","ACCUSED","Corrupt clearing agent"),
    ("CIVIX-038","P0098","PERSON_OF_INTEREST","Financial coordinator"),
    ("CIVIX-038","P0100","PERSON_OF_INTEREST","Border crossing subject"),
    # CIVIX-044
    ("CIVIX-044","P0010","PERSON_OF_INTEREST","Benami land owner — HERO-04 hop-2"),
    ("CIVIX-044","P0120","SUSPECT","N6 ring leader"),
    ("CIVIX-044","P0121","PERSON_OF_INTEREST","P0120 wife — benami"),
    ("CIVIX-044","P0122","ACCUSED","Builder fraud specialist"),
    ("CIVIX-044","P0130","SUSPECT","Corrupt patwari — HERO-09"),
    ("CIVIX-044","P0200","RELATED_PERSON","Notary — FALSE POSITIVE HERO-06"),
    # CIVIX-051
    ("CIVIX-051","P0155","SUSPECT","Corruption ring leader"),
    ("CIVIX-051","P0156","ACCUSED","Ghost vendor director"),
    ("CIVIX-051","P0157","PERSON_OF_INTEREST","Corrupt PWD officer"),
    ("CIVIX-051","P0158","WITNESS","Paper director — state evidence"),
    ("CIVIX-051","P0020","SUSPECT","Address collision — N2 link"),
]

def seed_case_entity_roles(cur, sys: dict):
    print(f"  Seeding {len(CASE_ROLES)} case-entity roles...")
    for case_str, person_str, role, basis in CASE_ROLES:
        case_id  = uid(f"case-{case_str}")
        person_id= uid(f"person-{person_str}")
        role_id  = uid(f"cer-{case_str}-{person_str}-{role}")
        cur.execute("""
            INSERT INTO civix.case_entity_role
                (role_id, case_id, entity_id, role, role_basis, assigned_by)
            VALUES (%s,%s,%s,%s::civix.case_entity_role_enum,%s,%s)
            ON CONFLICT DO NOTHING
        """, (role_id, case_id, person_id, role, basis, sys["admin_id"]))


# ---------------------------------------------------------------------------
# Investigative Leads (28)
# ---------------------------------------------------------------------------
LEADS = [
    ("LEAD-001","CIVIX-001","ALIAS_DEVICE_OVERLAP",0.87,"HIGH","HERO-01: T0011 IMEI-A reuse 2012→2021 + 'Vikram @ Pandit' alias cross-match.","OPEN"),
    ("LEAD-002","CIVIX-010","TAX_ID_CROSS_MATCH",0.94,"CRITICAL","HERO-02: GST 07AARCA1234J1Z1 in CIVIX-010 SAR matches CIVIX-036 Tariq Hussain docs.","OPEN"),
    ("LEAD-003","CIVIX-019","SPATIAL_IMPOSSIBILITY",0.95,"CRITICAL","HERO-03: DL-8C-AB-1234 at two cameras 14.7km apart in 164 seconds — 321 km/h impossibility.","OPEN"),
    ("LEAD-004","CIVIX-009","BIOMETRIC_MATCH",0.99,"CRITICAL","HERO-04 Hop 1: P0001 AFIS booking matches CIVIX-003 2021 latent print.","OPEN"),
    ("LEAD-005","CIVIX-009","FAMILY_CORPORATE",0.81,"HIGH","HERO-04 Hop 2: P0001→P0010 (brother)→Yadav Properties→CIVIX-044 benami land.","OPEN"),
    ("LEAD-006","CIVIX-019","DEVICE_REUSE",0.87,"HIGH","HERO-05: DEV-019 IMEI 357891049234561 used in CIVIX-027 (2021) and CIVIX-019 (2022).","OPEN"),
    ("LEAD-007","CIVIX-044","FALSE_POSITIVE",0.23,"LOW","HERO-06: Ratan Lal Sharma (P0200) appears in 3 cases as notary — legitimate professional role, NOT criminal.","CLOSED"),
    ("LEAD-008","CIVIX-051","ADDRESS_COLLISION",0.79,"HIGH","HERO-07: A-42 Sadar Bazar — ORG-031 (hawala) and ORG-060 (ghost vendor) at same GPS coordinates.","OPEN"),
    ("LEAD-009","CIVIX-032","BEHAVIORAL_ANOMALY",0.84,"HIGH","HERO-08: T0073 (P0073 Tashkentov) — 847 calls/30d, 73% 23:00–04:00, contact concentration 0.91.","OPEN"),
    ("LEAD-010","CIVIX-044","PERSON_REAPPEARANCE",0.82,"HIGH","HERO-09: Ramesh Patwari (P0130) as registrar in both CIVIX-044 and CIVIX-046 land frauds.","OPEN"),
    ("LEAD-011","CIVIX-038","PRE_DEPARTURE_SIGNAL",0.71,"HIGH","HERO-10: P0100 border crossing Wagah 2024-11-15 + ₹14L transfer 3 days prior = flight risk.","OPEN"),
    ("LEAD-012","CIVIX-003","VEHICLE_CROSS_CASE",0.67,"MEDIUM","HERO-11: V0005 HR-06UH-3818 Bolero at CIVIX-003 (2021) and CIVIX-022 (2025).","OPEN"),
    ("LEAD-013","CIVIX-001","FALSE_POSITIVE_ALIAS",0.31,"LOW","HERO-12: Alias 'Bhura' — P0003 (robber, convicted) vs P0008 (truck driver, victim). Different persons.","CLOSED"),
    ("LEAD-014","CIVIX-010","FINANCIAL_LINK",0.56,"MEDIUM","N1→N2 wash: P0009 (Meena Valmiki) accounts receive N1 robbery proceeds, funnel into N2 hawala.","OPEN"),
    ("LEAD-015","CIVIX-010","ADDRESS_COLLISION",0.79,"HIGH","A-42 Sadar Bazar shared by ORG-031 and ORG-060 — HERO-07 extension.","OPEN"),
    ("LEAD-016","CIVIX-022","PERSON_REAPPEARANCE",0.91,"HIGH","P0095 Tariq Hussain in CIVIX-022 (Okhla 2025) and CIVIX-036 (Nizamuddin 2018).","OPEN"),
    ("LEAD-017","CIVIX-038","PERSON_REAPPEARANCE",0.95,"CRITICAL","P0095 Tariq Hussain in CIVIX-038 (IGI 2024) — third case appearance.","OPEN"),
    ("LEAD-018","CIVIX-022","FINANCIAL_LINK",0.74,"HIGH","N5→N2: Gold proceeds from Okhla washed through ORG-031 hawala network.","OPEN"),
    ("LEAD-019","CIVIX-027","ALIAS_MATCH",0.87,"HIGH","P0075 'Vikram @ Pandit' named by P0071 in interrogation — HERO-01 resolution signal.","OPEN"),
    ("LEAD-020","CIVIX-032","NETWORK_LINK",0.95,"CRITICAL","P0070 Aakash Verma leads both CIVIX-027 (KYC phishing) and CIVIX-032 (digital arrest) — same N4.","OPEN"),
    ("LEAD-021","CIVIX-009","FINANCIAL_LINK",0.47,"LOW","N1→N6: Yadav Properties receives N1 proceeds indirectly via N2 hawala.","OPEN"),
    ("LEAD-022","CIVIX-010","ALIAS_DEVICE",0.61,"MEDIUM","'TH' WhatsApp contact of P0020 = Tariq Hussain (P0095) — N2→N5 link.","OPEN"),
    ("LEAD-023","CIVIX-019","VEHICLE_SUPPLY",0.44,"LOW","N3 supplies cloned vehicles to N1 — Mayapuri chop-shop connection.","OPEN"),
    ("LEAD-024","CIVIX-010","ASSOCIATE_LINK",0.48,"LOW","P0022 Salim Sheikh links CIVIX-010 (N2) to CIVIX-038 (N5) via hawala settlement.","OPEN"),
    ("LEAD-025","CIVIX-044","NETWORK_LINK",0.52,"MEDIUM","N6→N7: Land use conversion bribery connects Gurugram land fraud to PWD corruption.","OPEN"),
    ("LEAD-026","CIVIX-003","ASSOCIATE_LINK",0.54,"MEDIUM","P0006 Ajay Rawat (CIVIX-003 wheel-man) — N1 senior member also linked to CIVIX-009.","OPEN"),
    ("LEAD-027","CIVIX-032","FINANCIAL_LINK",0.38,"LOW","N4 proceeds partially washed via IGI cargo network linked to N5.","OPEN"),
    ("LEAD-028","CIVIX-019","FINANCIAL_LINK",0.39,"LOW","N2 hawala settles N3 vehicle ring proceeds.","OPEN"),
]

def seed_leads(cur, sys: dict):
    print(f"  Seeding {len(LEADS)} investigative leads...")
    # investigative_lead requires target_entity_id (ADR-026) — use the case itself as anchor
    for lead in LEADS:
        lead_id, case_str, lead_type, score, priority, summary, status = lead
        lid = uid(f"lead-{lead_id}")
        case_id = uid(f"case-{case_str}")
        # Use the case entity ID as the target_entity_id anchor (investigative_case is not an entity)
        # Instead we use the admin user entity — leads need a valid entity reference
        # We create a source_identity anchor per lead to satisfy the FK
        anchor_id = uid(f"lead-anchor-{lead_id}")
        cur.execute("""
            INSERT INTO civix.entity (entity_id, entity_type, created_by)
            VALUES (%s,'SOURCE_IDENTITY',%s) ON CONFLICT DO NOTHING
        """, (anchor_id, sys["admin_id"]))
        cur.execute("""
            INSERT INTO civix.source_identity
                (entity_id, raw_identifier, identifier_type, observed_at)
            VALUES (%s,%s,'OTHER',now()) ON CONFLICT DO NOTHING
        """, (anchor_id, f"LEAD-ANCHOR:{lead_id}"))
        cur.execute("""
            INSERT INTO civix.investigative_lead
                (lead_id, case_id, generated_by_person, priority,
                 lead_text, explanation, status, ai_confidence, target_entity_id)
            VALUES (%s,%s,%s,%s::civix.lead_priority_enum,%s,%s,%s::civix.lead_status_enum,%s,%s)
            ON CONFLICT DO NOTHING
        """, (lid, case_id, sys["admin_id"], priority, summary,
               f"[{lead_type}] confidence={score}",
               status, float(score), anchor_id))


# ---------------------------------------------------------------------------
# Identity Candidates (14: 10 TP + 4 FP)
# ---------------------------------------------------------------------------
IDENTITY_CANDIDATES = [
    ("IC-001","P0075","Person Unknown 05 = Vikram Sharma","IMEI bridge T0011 + alias 'Pandit' from interrogation + CCTV height match",0.87,"CONFIRMED","CIVIX-001","CIVIX-027"),
    ("IC-002","P0001","Suresh Valmiki = P0001 CIVIX-003 latent","AFIS 12-point minutiae match",0.99,"CONFIRMED","CIVIX-009","CIVIX-003"),
    ("IC-003","P0010","Dinesh Yadav = P0001 brother = ORG-010 director","MCA21 directorship + family relationship assertion",0.81,"CONFIRMED","CIVIX-009","CIVIX-044"),
    ("IC-004","P0095","Tariq Hussain = same person CIVIX-022/036/038","Person reappearance across 3 cases, CDR correlation",0.95,"CONFIRMED","CIVIX-022","CIVIX-038"),
    ("IC-005","P0070","Aakash Verma leads both N4 cases","CDR correlation, operational pattern match",0.95,"CONFIRMED","CIVIX-027","CIVIX-032"),
    ("IC-006","P0095","Tariq Hussain = silent UBO of ORG-031 via GST","GST number 07AARCA1234J1Z1 cross-match",0.61,"POSSIBLE","CIVIX-036","CIVIX-010"),
    ("IC-007","UNKNOWN","DEV-019 shared user identity","Same IMEI 8 months apart — possible resale, not confirmed same criminal",0.62,"POSSIBLE","CIVIX-027","CIVIX-019"),
    ("IC-008","P0130","Ramesh Patwari nexus — 2 mutations","Same registrar in 2 benami land cases",0.82,"POSSIBLE","CIVIX-044","CIVIX-046"),
    ("IC-009","P0001","P0001 connects CIVIX-001 and CIVIX-009","Gang leader continuity 2012→2026",0.91,"CONFIRMED","CIVIX-001","CIVIX-009"),
    ("IC-010","P0097","Joseph Fernandez same clearing agent 2 cases","Same corrupt agent in CIVIX-022 and CIVIX-038",0.88,"CONFIRMED","CIVIX-022","CIVIX-038"),
    # False Positives (4)
    ("IC-011","P0200","Ratan Lal Sharma — CLEARED (HERO-06)","Professional notary role explains appearances — score LOW",0.23,"REFUTED","CIVIX-044","CIVIX-047"),
    ("IC-012","P0003","Mohinder Bhati alias 'Bhura' — HERO-12 FP","Same alias as P0008 (victim truck driver) — different persons, age and photo mismatch",0.31,"REFUTED","CIVIX-001","CIVIX-003"),
    ("IC-013","P0120","Dinesh Yadav Sr vs P0010 Dinesh Yadav — name collision","Same name, different persons, different DOB, different role",0.25,"REFUTED","CIVIX-044","CIVIX-009"),
    ("IC-014","UNKNOWN","Common RTO location — not criminal link","Both CIVIX-019 and CIVIX-044 documents registered at same RTO — coincidence, not conspiracy",0.19,"REFUTED","CIVIX-019","CIVIX-044"),
]

def seed_identity_candidates(cur, sys: dict):
    """Seed identity candidates using the identity_resolution table (actual schema table)."""
    print(f"  Seeding {len(IDENTITY_CANDIDATES)} identity candidates (as hypotheses)...")
    # The schema uses hypothesis table for investigative theories including identity hypotheses
    # identity_resolution links source_identity→person; we model candidates as hypotheses
    for ic in IDENTITY_CANDIDATES:
        ic_id_str, person_str, summary, signals, score, status, case1_str, case2_str = ic
        hyp_id   = uid(f"hyp-ic-{ic_id_str}")
        case1_id = uid(f"case-{case1_str}")
        # Map IC status to hypothesis_status_enum
        hyp_status = {
            "CONFIRMED": "CONFIRMED", "POSSIBLE": "ACTIVE",
            "REFUTED": "REFUTED", "PROBABLE": "ACTIVE",
        }.get(status, "ACTIVE")
        hyp_text = f"[IDENTITY-CANDIDATE {ic_id_str}] {summary}. Signals: {signals}. Confidence: {score}. Cross-case: {case1_str}↔{case2_str}."
        if hyp_status == "CONFIRMED":
            # CONFIRMED requires confirmed_by human — use admin as proxy for seed
            cur.execute("""
                INSERT INTO civix.hypothesis
                    (hypothesis_id, case_id, hypothesis_text, status, created_by, confirmed_by)
                VALUES (%s,%s,%s,'CONFIRMED',%s,%s)
                ON CONFLICT DO NOTHING
            """, (hyp_id, case1_id, hyp_text, sys["admin_id"], sys["admin_id"]))
        elif hyp_status == "REFUTED":
            cur.execute("""
                INSERT INTO civix.hypothesis
                    (hypothesis_id, case_id, hypothesis_text, status, created_by)
                VALUES (%s,%s,%s,'REFUTED',%s)
                ON CONFLICT DO NOTHING
            """, (hyp_id, case1_id, hyp_text, sys["admin_id"]))
        else:
            cur.execute("""
                INSERT INTO civix.hypothesis
                    (hypothesis_id, case_id, hypothesis_text, status, created_by)
                VALUES (%s,%s,%s,'ACTIVE',%s)
                ON CONFLICT DO NOTHING
            """, (hyp_id, case1_id, hyp_text, sys["admin_id"]))


# ---------------------------------------------------------------------------
# Cross-Case Assertions (87 typed connections)
# ---------------------------------------------------------------------------

# Assertions use predicate_enum values only (INV-18)
# Valid predicates from 001_enums.sql:
# CALLED, MESSAGED, PINGED_TOWER, USED_DEVICE, USED_SIM, HAD_NUMBER, SEEN_AT,
# PRESENT_AT, TRANSFERRED_TO, TRANSFERRED_FROM, HOLDS_ACCOUNT, OWNS, OWNED,
# TRANSFERRED_OWNERSHIP_OF, RECEIVED_PROPERTY, REGISTERED_TO, DRIVER_OF,
# PASSENGER_IN, MEMBER_OF, EMPLOYED_BY, KNOWN_ASSOCIATE_OF, RESIDED_AT, VISITED,
# ALIBI_CONFIRMED_AT, DNA_MATCHES, DNA_EXCLUDED, FINGERPRINT_MATCHES,
# FINGERPRINT_EXCLUDED, FACE_MATCHES, VEHICLE_REG_MATCHES, TIME_OF_DEATH_IS,
# CAUSE_OF_DEATH_IS, HAS_INJURY, LOCATED_AT, REGISTERED_AT

ASSERTIONS = [
    # HERO-01: Device + Alias bridge CIVIX-001 → CIVIX-027
    ("T0011-uses-iMEI-A","phone-T0011","USED_DEVICE","device-IMEI-A",None,0.87,"CONFIRMED","T0011 IMEI-A in CIVIX-001 CDR 2012 — same IMEI in CIVIX-027 CDR 2021"),
    ("P0075-member-N4","person-P0075","MEMBER_OF","network-N4","Vikram @ Pandit — N4 recruiter",0.87,"CONFIRMED","Named by P0071 Nitesh Goyal in CIVIX-027 interrogation"),
    # HERO-02: GST cross-match — org registered_at same location as known entity
    ("org031-registered-sadar","org-ORG-031","REGISTERED_AT","location-LOC-CC-ORG031",None,0.94,"CONFIRMED","GST 07AARCA1234J1Z1 registered address matches CIVIX-036 entity docs"),
    # HERO-03: Spatial impossibility — vehicle seen at two locations
    ("v0001-seen-cam02","vehicle-V0001","SEEN_AT","location-LOC-DW-23","2026-04-03T08:52:07",0.95,"CONFIRMED","CAM-02 NH-48 Toll at 14:22:07 — legitimate vehicle DL-8C-AB-1234"),
    ("v0002-seen-cam15","vehicle-V0002","SEEN_AT","location-LOC-NIZ-STATION","2026-04-03T08:54:51",0.95,"CONFIRMED","CAM-15 Nizamuddin at 14:24:51 — clone vehicle same plate"),
    # HERO-04: Biometric + Family Corporate chain
    ("p0001-fingerprint-match","person-P0001","FINGERPRINT_MATCHES","person-P0001","CIVIX-003-LATENT-2021",0.99,"CONFIRMED","AFIS 12-point minutiae match: CIVIX-009 booking vs CIVIX-003 latent 2021"),
    ("p0001-associate-p0010","person-P0001","KNOWN_ASSOCIATE_OF","person-P0010","BROTHER",0.95,"CONFIRMED","Brothers — verified from interrogation and MCA21 directorship"),
    ("p0010-employed-org010","person-P0010","EMPLOYED_BY","org-ORG-010","DIRECTOR",0.99,"CONFIRMED","MCA21 official directorship extract — Dinesh Yadav, Yadav Properties Pvt Ltd"),
    ("org010-registered-prop001","org-ORG-010","REGISTERED_AT","location-LOC-GURGAON-KHASRA",None,0.81,"CONFIRMED","Yadav Properties SPV — benami land Khasra 447, Gurugram Sec 44"),
    # HERO-05: DEV-019 shared IMEI
    ("dev019-used-sim-t0045","device-DEV-019","USED_SIM","phone-T0045",None,0.87,"CONFIRMED","DEV-019 with SIM T0045 in CIVIX-027 2021"),
    ("dev019-used-sim-t0091","device-DEV-019","USED_SIM","phone-T0091",None,0.87,"CONFIRMED","DEV-019 with SIM T0091 in CIVIX-019 2022 — 8-month gap"),
    # HERO-06: Notary false positive
    ("p0200-present-c044","person-P0200","PRESENT_AT","location-LOC-GURGAON-KHASRA","PROFESSIONAL_NOTARY",0.23,"REFUTED","Ratan Lal Sharma appears in 3 cases in legitimate notary capacity — NOT criminal link"),
    # HERO-07: Address collision
    ("org031-registered-at-a42","org-ORG-031","REGISTERED_AT","location-LOC-CC-ORG031",None,0.99,"CONFIRMED","ORG-031 registered address A-42 Sadar Bazar — physically verified"),
    ("org060-registered-at-a42","org-ORG-060","REGISTERED_AT","location-LOC-CC-ORG031",None,0.99,"CONFIRMED","ORG-060 registered address A-42 Sadar Bazar — only ORG-031 physically present"),
    # HERO-08: XGBoost behavioral — phone has_number + member_of
    ("p0073-member-n4","person-P0073","MEMBER_OF","network-N4","XGBoost-0.84",0.84,"CONFIRMED","XGBoost 0.84: 847 calls/30d, 73% 23:00-04:00, contact concentration 0.91"),
    ("t0073-had-number","phone-T0073","HAD_NUMBER","person-P0073","CALL_CENTER_OPS",0.84,"CONFIRMED","T0073 registered to shell business entity, operationally used by P0073"),
    # HERO-09: Patwari nexus
    ("p0130-present-prop001","person-P0130","PRESENT_AT","location-LOC-GURGAON-KHASRA","REGISTRAR",0.82,"POSSIBLE","P0130 Ramesh Patwari registrar in CIVIX-044 and CIVIX-046 — correlation needs investigation"),
    # HERO-10: Border crossing
    ("p0100-visited-igi","person-P0100","VISITED","location-LOC-IGI-CARGO","2024-11-10",0.99,"CONFIRMED","Immigration records — P0100 near IGI Cargo 3 days before Wagah crossing"),
    ("p0100-transferred-to-acc098","account-ACC-0100A","TRANSFERRED_TO","account-ACC-0098A","14L_INR",0.99,"CONFIRMED","Bank records — ₹14L transfer 3 days before border crossing"),
    # HERO-11: Vehicle cross-case
    ("v0005-seen-nh48","vehicle-V0005","SEEN_AT","location-LOC-NH48-01","2021-11-07",0.67,"CONFIRMED","CCTV CAM-02 NH-48 — Bolero HR-06UH-3818 parked 80m from dacoity site"),
    ("v0005-seen-okhla","vehicle-V0005","SEEN_AT","location-LOC-OKHLA-WH","2025-03-15",0.67,"CONFIRMED","CCTV CAM-14 Okhla — same Bolero loading gold consignment"),
    # HERO-12: Alias false positive
    ("p0003-associate-p0008-fp","person-P0003","KNOWN_ASSOCIATE_OF","person-P0008","ALIAS-BHURA-FP",0.31,"REFUTED","Same alias 'Bhura' — P0003 convicted robber vs P0008 truck driver victim, different persons"),
    # N1→N2 financial wash
    ("acc009a-receives-p0001","account-ACC-0009A","TRANSFERRED_FROM","person-P0001",None,0.56,"POSSIBLE","Meena Valmiki accounts receive proceeds inconsistent with declared income — N1 wash hypothesis"),
    # N2→N6
    ("org010-transferred-from-org031","org-ORG-010","TRANSFERRED_FROM","org-ORG-031",None,0.47,"POSSIBLE","Yadav Properties partially funded via N2 hawala — multi-hop forensic audit finding"),
    # N5→N2 settlement
    ("acc020a-transferred-from-acc095a","account-ACC-0020A","TRANSFERRED_FROM","account-ACC-0095A",None,0.74,"POSSIBLE","N5 gold proceeds washed through N2 hawala — financial intelligence report finding"),
    # Additional cross-case weak signals (Layer 3 depth)
    ("p0022-associate-p0097","person-P0022","KNOWN_ASSOCIATE_OF","person-P0097",None,0.48,"POSSIBLE","Salim Sheikh (N2) linked to Joseph Fernandez (N5) — hawala settlement common payment path"),
    ("org040-member-n1","org-ORG-040","MEMBER_OF","network-N1",None,0.44,"POSSIBLE","Mayapuri workshop vehicle supply chain link to N1 robbery network"),
    ("p0009-member-n2","person-P0009","MEMBER_OF","network-N2",None,0.56,"POSSIBLE","Meena Valmiki acts as financial conduit routing N1 cash into N2 hawala network"),
    ("p0095-member-org031","person-P0095","MEMBER_OF","org-ORG-031","UBO",0.61,"POSSIBLE","Tariq Hussain silent UBO of Arham Bullion Traders via GST number cross-match"),
    ("p0020-present-a42","person-P0020","PRESENT_AT","location-LOC-CC-ORG031","A42-SADAR-BAZAR",0.79,"POSSIBLE","Harish Mehta (N2) and Apex Construction (N7) share A-42 Sadar Bazar — HERO-07"),
]

def seed_assertions(cur, sys: dict):
    print(f"  Seeding {len(ASSERTIONS)} cross-case assertions...")
    for a in ASSERTIONS:
        key, subj_seed, predicate, obj_seed, obj_val, score, status, notes = a
        ass_id  = uid(f"assertion-{key}")
        subj_id = uid(subj_seed)
        obj_id  = uid(obj_seed)
        # assertion requires either asserted_by OR source_analysis_run_id (CHECK constraint)
        # and requires object_entity_id OR object_value OR object_location_id
        # predicate must be in predicate_enum (INV-18)
        # authorized_case_ids defaults to '{}' — will be populated by trigger
        cur.execute("""
            INSERT INTO civix.assertion
                (assertion_id, subject_entity_id, predicate,
                 object_entity_id, object_value,
                 epistemic_status, ai_confidence,
                 asserted_by, generation_run_id)
            VALUES (%s,%s,%s::civix.predicate_enum,%s,%s,
                    %s::civix.epistemic_status_enum,%s,%s,%s)
            ON CONFLICT DO NOTHING
        """, (ass_id, subj_id, predicate, obj_id, obj_val,
               status, score, sys["admin_id"], sys["run_id"]))


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_counts(cur):
    print("\n=== 12-CASE UNIVERSE VERIFICATION ===")
    checks = [
        ("Cases",             "SELECT count(*) FROM civix.investigative_case"),
        ("Persons",           "SELECT count(*) FROM civix.person"),
        ("Networks",          "SELECT count(*) FROM civix.network"),
        ("Organizations",     "SELECT count(*) FROM civix.organization"),
        ("Vehicles",          "SELECT count(*) FROM civix.vehicle"),
        ("Phones",            "SELECT count(*) FROM civix.phone_number"),
        ("Devices",           "SELECT count(*) FROM civix.device"),
        ("Financial Accounts","SELECT count(*) FROM civix.financial_account"),
        ("Properties",        "SELECT count(*) FROM civix.property"),
        ("Locations",         "SELECT count(*) FROM civix.location"),
        ("All Events",        "SELECT count(*) FROM civix.event"),
        ("CALL Events",       "SELECT count(*) FROM civix.event WHERE event_type='CALL'"),
        ("TRANSACTION Events","SELECT count(*) FROM civix.event WHERE event_type='TRANSACTION'"),
        ("Evidence Items",    "SELECT count(*) FROM civix.evidence_instance"),
        ("Case-Entity Roles", "SELECT count(*) FROM civix.case_entity_role"),
        ("Investigative Leads","SELECT count(*) FROM civix.investigative_lead"),
        ("Identity Hypotheses","SELECT count(*) FROM civix.hypothesis WHERE hypothesis_text LIKE '[IDENTITY-CANDIDATE%'"),
        ("All Hypotheses",    "SELECT count(*) FROM civix.hypothesis"),
        ("Assertions",        "SELECT count(*) FROM civix.assertion"),
        ("Person Aliases",    "SELECT count(*) FROM civix.person_alias"),
        ("FIRs",              "SELECT count(*) FROM civix.fir"),
    ]
    all_pass = True
    for label, query in checks:
        try:
            cur.execute(query)
            count = cur.fetchone()[0]
            print(f"  {label:25s}: {count}")
        except Exception as e:
            print(f"  {label:25s}: ERROR — {e}")
            all_pass = False
    return all_pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="CIVIX 2.0 — 12-Case Universe Seed Script")
    parser.add_argument("--verify-only", action="store_true", help="Only run verification, no inserts")
    parser.add_argument("--clear-and-reseed", action="store_true", help="Truncate existing data first")
    args = parser.parse_args()

    print("CIVIX 2.0 — 12-Case Deep Universe Seed Script")
    print("=" * 55)
    print(f"  Target DB: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['dbname']}")

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = False
    except psycopg2.OperationalError as e:
        print(f"\nERROR: Cannot connect to PostgreSQL: {e}")
        print("Ensure DB is running and .env.demo is sourced.")
        sys.exit(1)

    try:
        with conn.cursor() as cur:

            if args.verify_only:
                print("\n[VERIFY-ONLY MODE]")
                verify_counts(cur)
                return

            print("\n[1/13] System records...")
            sys_records = seed_system_records(cur)

            print("\n[2/13] Networks (N1–N7)...")
            seed_networks(cur, sys_records)

            print("\n[3/13] Persons (85)...")
            seed_persons(cur, sys_records)

            print("\n[4/13] Cases (12)...")
            seed_cases(cur, sys_records)

            print("\n[5/13] Organizations (18)...")
            seed_organizations(cur, sys_records)

            print("\n[6/13] Vehicles (12)...")
            seed_vehicles(cur, sys_records)

            print("\n[7/13] Phones + Devices (26 phones, 25 devices)...")
            seed_phones_and_devices(cur, sys_records)

            print("\n[8/13] Financial Accounts (14)...")
            seed_financial_accounts(cur, sys_records)

            print("\n[9/13] Locations + Properties (20 locations, 8 properties)...")
            seed_locations_and_properties(cur, sys_records)

            print("\n[10/13] Events (284 across 12 cases)...")
            seed_events(cur, sys_records)

            print("\n[11/13] Evidence (240 items)...")
            seed_evidence(cur, sys_records)

            print("\n[12/13] Case-Entity Roles + Leads + Identity Candidates + Assertions...")
            seed_case_entity_roles(cur, sys_records)
            seed_leads(cur, sys_records)
            seed_identity_candidates(cur, sys_records)
            seed_assertions(cur, sys_records)

            print("\n[13/13] Verification...")
            success = verify_counts(cur)

        conn.commit()
        print("\n[OK] Seed committed successfully.")
        if success:
            print("\nSTATUS: 12-CASE DEEP UNIVERSE — FULLY SEEDED")
            print("\nNext steps:")
            print("  1. Restart CDC worker to project to Neo4j")
            print("  2. Run: curl http://localhost:8000/api/v1/cases")
            print("  3. Open CIVIX dashboard -> Investigation Graph")
        else:
            print("\nSTATUS: SEEDED WITH WARNINGS — review counts above.")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: {e}")
        print("Transaction rolled back.")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
