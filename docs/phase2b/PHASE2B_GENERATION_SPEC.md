# CIVIX — PHASE 2B GENERATION SPEC
## Canonical World-to-PostgreSQL Mapping Specification

**Version**: 1.0 | **Date**: 2026-08-29
**Authority**: SYNTHETIC_DATA_ENGINE_DESIGN.md, 03_DATABASE_SCHEMA_BIBLE.md, 12_SYNTHETIC_DATA_BIBLE.md

---

## 1. Source Mapping

### 1.1 Canonical Sources (inserted once, reused by all records)

| Source Name | agency_type | Provides |
|---|---|---|
| `Jio Telecom` | TELECOM | cdrs.csv |
| `SBI Bank` | BANK | transactions.csv (SBI-* accounts) |
| `HDFC Bank` | BANK | transactions.csv (HDFC-* accounts) |
| `PNB Bank` | BANK | transactions.csv (PNB-* accounts) |
| `BOI Bank` | BANK | transactions.csv (BOI-* accounts) |
| `BOB Bank` | BANK | transactions.csv (BOB-* accounts) |
| `ICICI Bank` | BANK | transactions.csv (ICICI-* accounts) |
| `Ajmer Revenue Office` | REVENUE_OFFICE | property_transfers.csv |
| `Ajmer Police` | POLICE | criminal_history_records.csv |
| `CCTV-Grid-Alpha` | CCTV_SYSTEM | surveillance_reports.json |
| `Traffic Control` | POLICE | vehicle_sightings.csv |
| `Confidential Informant CI-01` | INFORMANT | intelligence_reports.json (is_identity_protected=TRUE) |

### 1.2 CDR Mapping (cdrs.csv → PostgreSQL)

| CSV Field | PostgreSQL Target | Notes |
|---|---|---|
| `record_id` | `source_record.external_reference` | |
| `timestamp` | `event.occurred_at` lower bound | Upper = lower + duration_sec |
| `caller_msisdn` | `source_identity(identifier_type=PHONE_MSISDN)` | New SI created if not seen before |
| `caller_imei` | `source_identity(identifier_type=IMEI)` | `UNKNOWN-IMEI` → SI, not device |
| `receiver_msisdn` | `source_identity(identifier_type=PHONE_MSISDN)` | |
| `receiver_imei` | `source_identity(identifier_type=IMEI)` | |
| `duration_sec` | Event `occurred_at` interval width | |
| `location_cell` | `event_participant(CELL_TOWER, entity=location[cell])` | |

**Event type**: `CALL`
**Participants per CDR**: CALLER, CALLEE, CELL_TOWER (3 minimum)

### 1.3 Transaction Mapping (transactions.csv → PostgreSQL)

| CSV Field | PostgreSQL Target | Notes |
|---|---|---|
| `record_id` | `source_record.external_reference` | |
| `timestamp` | `event.occurred_at` | Point-in-time, 1-minute interval |
| `sender_account` | `financial_account.masked_number` OR `source_identity(OTHER)` | Non-ACC-* strings → SI |
| `receiver_account` | Same as sender_account logic | |
| `amount` | `observation.structured_content.amount_inr` | |
| `currency` | `observation.structured_content.currency` | |

**Event type**: `TRANSACTION`
**Participants**: SENDER (account entity), RECEIVER (account entity)

**Special cases**:
- `"Network Beta)"` → `source_identity(identifier_type=OTHER, raw_identifier="Network Beta)")`
- `"Malhotra Trading Co.)"` → `source_identity(identifier_type=OTHER, raw_identifier="Malhotra Trading Co.)")`
- `"minimal balance)"` → `source_identity(identifier_type=OTHER, raw_identifier="minimal balance)")`

### 1.4 Property Transfer Mapping (property_transfers.csv → PostgreSQL)

**H4 Critical Rule**: The 3 CSV rows represent 3 SEPARATE property mutation events in the CSV, but the architecture requires a SINGLE event with MULTIPLE target_property participants for H4 (PROP-01 + PROP-08 in same event). Resolution:
- PROP-TX-000001 (PROP-01, Khasra 45) → Event E_h4, participant TARGET_PROPERTY PROP-01
- PROP-08 (Khasra 45 adjacent parcel) → SAME Event E_h4, participant TARGET_PROPERTY PROP-08
- PROP-TX-000002 (PROP-02) → Separate event
- PROP-TX-000003 (PROP-03) → Separate event

**Canonical PROP-08**: The property `PROP-08` represents the adjacent Khasra 45 parcel that is also transferred in the same mutation event. It must be created as a `property` entity even though it only appears implicitly in the canonical world. This is the H4 resolution.

> [!IMPORTANT]
> H4 mandates: PROP-01 + PROP-08, both representing land at Khasra 45, in one single PROPERTY_MUTATION event. DO NOT use PROP-04. DO NOT split into two events.

| CSV Field | PostgreSQL Target |
|---|---|
| `record_id` | `source_record.external_reference` |
| `date` | `event.occurred_at = tstzrange(date, date + 1 day)` |
| `property_id` | `event_participant(TARGET_PROPERTY, property entity)` |
| `previous_owner_id` | `event_participant(PREVIOUS_OWNER, person entity)` |
| `new_owner_id` | `event_participant(NEW_OWNER, person entity)` |
| `registrar_office` | `event_participant(REGISTRAR, location entity)` |

### 1.5 Surveillance Report Mapping (surveillance_reports.json → PostgreSQL)

**Event type**: `SURVEILLANCE_OBSERVATION`
- Creates `observation` from surveillance text
- Creates `extraction(type=TEMPORAL_INFERENCE)` for person-location claims
- Does NOT create assertions directly (requires human analyst review)

### 1.6 Vehicle Sighting Mapping (vehicle_sightings.csv → PostgreSQL)

**Event type**: `VEHICLE_SIGHTING`
- Participant: SUBJECT (vehicle entity), LOCATION (location entity)
- No DRIVER required if driver not identified (GAP-18 resolution)

### 1.7 Criminal History Mapping (criminal_history_records.csv → PostgreSQL)

| Field | Mapping |
|---|---|
| Person + status=Acquitted | `case_entity_role(role=ACQUITTED)` for the referenced historical case |
| No `is_criminal` column created | INV-17 strictly enforced |

### 1.8 Intelligence Report Mapping (intelligence_reports.json → PostgreSQL)

- Source: `Confidential Informant CI-01` with `is_identity_protected=TRUE`
- Creates `source_record`, `evidence_artifact`, `evidence_instance`
- Creates `observation(observer_type='HUMAN', observation_text=report_text)`
- Creates `extraction(type=NER)` for entity mentions
- Does NOT automatically create assertions (NER extractions require analyst review)

---

## 2. Location Master Mapping (location_master.json → PostgreSQL)

All `CELL-*` and `LOC-*` references from CDRs and surveillance reports map to `civix.location` entities with PostGIS GEOMETRY.

| Location Type | location_type_enum | GEOMETRY |
|---|---|---|
| CELL-01 through CELL-47 | CELL_SECTOR_POLYGON | POLYGON (from location_master.json) |
| LOC-01 (Ajmer Revenue Office) | EXACT_POINT | POINT |
| LOC-02 (Ajmer Police Station) | EXACT_POINT | POINT |
| Building/address locations | EXACT_POINT or ESTIMATED_POINT | POINT |

---

## 3. SIM Assignment Generation

The canonical world defines SIM history in section 14 of `synthetic_world.md`. Each SIM assignment creates:
- `sim_in_device` row with `valid_time` TSTZRANGE
- `sim_number_assignment` row with `valid_time` TSTZRANGE

**Critical SIM Sharing Scenario** (CDR-based detection, SIG-adjacent):
- Ravi's SIM (MSISDN: 9555666777) used by Bhupendra's device (DEV-06) between Jun 15–Jun 28
- This creates CDRs where `caller_msisdn = 9555666777` but `caller_imei = IMEI-DEV-06`
- This mismatch is the investigative anomaly
- `sim_in_device` record must reflect: SIM assigned to Ravi's device NORMALLY, but CDR evidence shows it in Bhupendra's device → `data_quality_issue(type=CONTRADICTORY_DATA)` created

---

## 4. Assertion Generation (Full Pipeline Required)

For each CDR observation, generate exactly one assertion:
```
subject: source_identity(caller_msisdn)
predicate: CALLED
object: source_identity(receiver_msisdn)
epistemic_status: CONFIRMED (CDR is direct evidence)
valid_from: event.occurred_at lower bound
valid_to: event.occurred_at upper bound
asserted_by: NULL (AI-derived via analysis_run)
source_analysis_run_id: run_id of CDR analysis run
generation_run_id: run_id
```

For each transaction observation:
```
subject: source_identity(sender_account) OR financial_account
predicate: TRANSFERRED_TO
object: source_identity(receiver_account) OR financial_account
```

For each property mutation:
```
subject: person(new_owner)
predicate: RECEIVED_PROPERTY
object: property
```

---

## 5. Investigation Signal Injection

### SIG-03 (Suresh movement anomaly)
- Suresh (P-03) has CDRs pinging CELL towers in both Jaipur AND Ajmer regions within a 3-hour window.
- This appears in the existing `cdrs.csv` as anomalous cell IDs.
- The ingestion must map these to geographically distant `location` entities.
- Validation: ST_Distance between two pinged cells > 200km while event timestamps are <3 hours apart.

### SIG-05 (Dinesh ₹3.25L corruption deposits)
- Dinesh (P-11) receives 3 deposits of equal amounts (~₹108,333 each) at regular intervals.
- These appear in `transactions.csv`.
- Validation: COUNT of transactions to Dinesh's account WHERE amount BETWEEN 100000 AND 120000 = 3.

### SIG-06 (Deepak ₹75K deposit)
- Deepak (P-04) receives a single ₹75,000 transfer.
- Appears in `transactions.csv` (TX-000013: SBI-****8890 → SBI-****3312, amount=75000).
- Validation: EXISTS transaction with receiver=Deepak's account AND amount=75000.

### SIG-08 (Bhupendra/Gopal periodic communications)
- Bhupendra (P-10/P-15) calls Gopal (P-24) on 3 periodic dates (Jun 12, Jul 14, Aug 11).
- Appears in `cdrs.csv`.
- Validation: 3 CALL events between these two source_identities with roughly monthly intervals.

### FL-06 (Rekha Verma false lead)
- Rekha Verma has suspicious communication patterns matching the Alpha network.
- BUT counter-evidence exists: she is a telecom operator handling legitimate calls.
- This must be represented as:
  - `investigative_lead` for Rekha Verma with `status=FALSE_POSITIVE`
  - `hypothesis_support` with `stance=CONTRADICT` for the hypothesis linking her to Alpha
  - Counter-evidence assertion: `Rekha Verma EMPLOYED_BY Jio Telecom`

### H4 (Property mutation: PROP-01 + PROP-08)
- See Section 1.4 above.
- Validation in `verify_phase2b.py` test L.
