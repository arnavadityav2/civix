# Phase 6: Database Architecture Audit & Canonical Schema Definition

**Date**: 2026-08-30
**Status**: READ-ONLY AUDIT COMPLETE
**Outcome**: NOT READY — BLOCKERS REMAIN

---

## 1. Current-State Architecture

CIVIX employs a Polyglot Persistence architecture separating the transactional system of record from the analytical graph layer:

- **PostgreSQL 16**: The canonical transactional database and immutable system of record. Enforces ACID compliance, Bitemporal history, Row-Level Security (RLS), and Data Provenance.
- **Neo4j**: An analytical projection of PostgreSQL synchronized via a CDC (Change Data Capture) outbox pattern. Used exclusively for pathfinding, community detection, and complex graph traversals.

The synthetic data generation framework (`civix_generator`) currently outputs Parquet/CSV/JSON files representing a "Golden World" scenario. The generator’s internal object models (e.g., `Person.is_criminal`) contain omniscient ground truth that must be structurally segregated from the operational database schemas.

---

## 2. Canonical Entity Inventory

Based on `03_DATABASE_SCHEMA_BIBLE.md` and `04_DATA_MODEL_AND_ONTOLOGY.md`, the universal entity hierarchy is rooted in `civix.entity`. 

### The Entity Subtypes
*All subtypes inherit `entity_id (UUID)` as their PK and FK.*
- `person`: Canonical resolved human.
- `source_identity`: Raw identifier (e.g., MSISDN, Masked Aadhaar, Email).
- `phone_number`: Telecom MSISDN.
- `sim`: Physical SIM card (ICCID).
- `device`: Hardware device (IMEI, MAC).
- `financial_account`: Bank, UPI, or Wallet account.
- `vehicle`: Registered vehicle (Registration Num, VIN).
- `property`: Cadastral real estate.
- `organization`: Legal corporate/government entity.
- `network`: Analytical grouping (Criminal, Social).
- `location`: PostGIS Geometry (Point, Polygon, Cell Sector).

---

## 3. Complete Attribute Inventory (Core Operational Tables)

*Note: For brevity, standard audit fields (`created_at`, `tx_start`, etc.) are omitted but strictly required on all tables.*

- **person**: `display_name`, `date_of_birth`, `gender`, `nationality`, `is_deceased`, `deceased_at`, `notes`.
- **source_identity**: `raw_identifier`, `identifier_type` (ENUM), `source_record_id`, `observed_at`.
- **phone_number**: `msisdn`, `country_code`, `operator`, `number_type`.
- **sim**: `iccid`, `imsi`, `issuing_operator`.
- **device**: `imei`, `mac_address`, `device_type`, `manufacturer`, `model`.
- **financial_account**: `masked_number`, `account_type`, `bank_name`, `ifsc_code`, `currency`.
- **vehicle**: `registration_number`, `vin`, `make`, `model`, `color`, `vehicle_type`, `registration_year`.
- **property**: `property_ref`, `property_type`, `area_sqm`, `description`, `boundary_geometry`.
- **organization**: `legal_name`, `org_type`, `registration_number`, `incorporation_date`, `jurisdiction`.
- **location**: `location_name`, `geometry` (PostGIS), `location_type` (ENUM), `uncertainty_radius_meters`.
- **investigative_case**: `case_id`, `case_number`, `title`, `case_type`, `status`, `priority`, `jurisdiction`, `opened_at`, `closed_at`.

---

## 4. Relationship Model

CIVIX relationships are modeled as temporal assertions and event participations rather than static FKs to accommodate uncertainty and change.

- **event_participant**: Links an `entity` to an `event` with a `participant_role` (e.g., CALLER, DRIVER).
- **assertion**: Links a Subject Entity to an Object Entity via a strongly-typed `predicate` (e.g., KNOWN_ASSOCIATE_OF, RESIDED_AT).
- **account_holder**: Temporal link between `financial_account` and `entity`.
- **sim_number_assignment** / **sim_in_device**: Bitemporal exclusion-constrained links representing telecom physical constraints.
- **hypothesis_support**: Links an `assertion` to an investigator's `hypothesis` with a `stance` (SUPPORT, CONTRADICT).

---

## 5. PostgreSQL Responsibility

PostgreSQL is the **only** database that applications write to. It is responsible for:
1. **Data Integrity**: Enforcing NOT NULL, UNIQUE, and CHECK constraints.
2. **Provenance**: Tracking the origin of every row (Human vs AI vs Source Data).
3. **Immutability**: Storing raw evidentiary records (`source_record`) immutably.
4. **Access Control**: Enforcing Row-Level Security via `case_access` tables.
5. **Outbox Management**: Triggering JSON payloads into `civix.outbox` upon entity mutations to feed Neo4j.

---

## 6. Neo4j Responsibility

Neo4j is an **analytical read-replica graph**. It is responsible for:
1. **Topological Algorithms**: PageRank, Louvain Community Detection.
2. **Pathfinding**: Shortest path between two seemingly unrelated entities.
3. **Graph Filtering**: Serving pre-filtered graph projections to ML models or UI dashboards.

**Graph Algorithm Safety Rule**: Neo4j structural algorithms MUST filter relationships by `stance='SUPPORT'`. `CONTRADICT` relationships are stored but must be excluded from algorithmic traversals.

---

## 7. Data Provenance Classification

All data must fall into one of these strict tiers:
- **Source/Government Data**: `source_record`, `evidence_instance`, `source_identity`. (Immutable ingest).
- **Transactional Data**: `phone_number`, `device`, `financial_account`. (Operational reality).
- **Derived Feature**: `extraction` (e.g., OCR from a document).
- **ML Prediction**: `identity_candidate`, `investigative_lead`. (Probabilistic).
- **Investigator-Entered Data**: `hypothesis`, `case_entity_role`, `identity_resolution`. (Human-asserted).
- **Audit/System Metadata**: `audit_event`, `civix_user`, `outbox`.
- **Synthetic/Test-Only**: `dataset`, `scenario`, `generation_run`.

---

## 8. Identity & Key Strategy

**CRITICAL RULE**: Aadhaar, PAN, SSN, and other government IDs are **NEVER** used as Primary Keys or exposed as system-level internal identifiers.

- **Primary Keys**: 100% `UUID` generated via `gen_random_uuid()` (v4).
- **Government IDs**: Modeled exclusively as `source_identity` rows with `identifier_type = 'AADHAAR_MASKED'` or `'PAN_MASKED'`. 
- **Reasoning**: Government IDs are subject to typographical errors, identity theft, and revocation. They are evidentiary claims, not structural database truths. Furthermore, storing raw Aadhaar numbers violates Indian IT Act compliance; hence they must be masked.

---

## 9. Security & Privacy Considerations

- **Row-Level Security (RLS)**: Must be enabled on all tables linking to a Case. `civix.current_user_id` must be SET LOCAL on the transaction.
- **Audit Trails**: `audit_event` must use an append-only trigger. Updates/Deletes on this table must be hard-blocked at the DB level.
- **Legal Expungement**: `legal_restriction` tables manage SEALED/EXPUNGED statuses, driving Neo4j `DETACH DELETE` cascades without deleting the PostgreSQL audit trail.

---

## 10. Temporal & History Strategy

- **System Time (tx_start / tx_end)**: Tracks when the database knew a fact. Managed by triggers.
- **Valid Time (valid_from / valid_to / TSTZRANGE)**: Tracks when the fact was true in the real world.
- **Immutability**: Source records, identity resolutions, and observations are strictly INSERT-only. Corrections create a new row linking back via `superseded_by`.

---

## 11. Synthetic vs Real Data Boundary (Conflicts Found!)

**CONFLICT IDENTIFIED**: The synthetic generator (`civix_generator/world/models.py`) creates `Person` objects with omniscient ground-truth attributes like `is_criminal = True` and properties with `fraudulent_buyer_id`.

**RESOLUTION**: These fields MUST NOT exist in PostgreSQL `civix.person` or `civix.property`. 
- In reality, guilt is a hypothesis until proven in court. 
- Synthetic labels will be ingested as `case_entity_role(role=SUSPECT)` and evaluated via ML, but the underlying table schema must remain neutral. 
- Synthetic ground truth must remain exclusively in the `scenario` tables or external Parquets.

---

## 12. Missing Requirements & Blockers

I have audited the Master Plan and Schema Bibles. Before DDL implementation can begin, the following blockers must be resolved:

1. **BLOCKER 1: Migration Tool Unselected**
   - The `19_IMPLEMENTATION_MASTER_PLAN.md` lists Phase 4 (Migration Tool Decision: Alembic vs Flyway vs Liquibase) as an **OPEN DECISION**.
   - DDL cannot be written until the tool is chosen, as Flyway requires raw `.sql` files while Alembic requires Python `op.create_table()` scripts.

2. **BLOCKER 2: Forensic Data MVP**
   - Phase 6 of the Master Plan lists the inclusion of synthetic forensic data as an **OPEN DECISION**. If tables like `medical_report` and `forensic_report` are to be included in the baseline DDL, their structure needs final sign-off.

---

## 13. Recommended Implementation Order

Once blockers are resolved, DDL must be executed in this exact dependency order:
1. Extensions (`postgis`, `uuid-ossp`)
2. Enums (`entity_type_enum`, etc.)
3. Users & Auth (`civix_user`)
4. Source & Evidence (`source`, `source_record`)
5. Universal Entity Supertype (`entity`)
6. Entity Subtypes (`person`, `phone_number`, etc.)
7. Telephony Constraints (`sim_number_assignment`)
8. Case Management (`investigative_case`)
9. Epistemic Pipeline (`event`, `assertion`, `hypothesis`)
10. System/Audit (`audit_event`, `outbox`)

---

# FINAL STATUS:
## PHASE 6 DATABASE ARCHITECTURE: NOT READY — BLOCKERS REMAIN
