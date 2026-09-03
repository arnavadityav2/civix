# CANONICAL PHASE 7 HANDOVER - EXHAUSTIVE TECHNICAL RECORD (10000+ Words Context)

**Status:** [HISTORICAL RECORD] IDE Agent Paused Mid-Task (Phase 7 Task 2).
**Current Verified Status:** Phase 7 Tasks 1, 2, and 3 are COMPLETE and ACCEPTED.
**Date:** 2026-08-30

> [!CAUTION]
> This is the canonical, highly exhaustive technical handover record for the Civix SIH 2026 project. 
> To the AI Agent reading this: YOU HAVE SUFFERED CONTEXT DRIFT. The user has explicitly generated this massive report to provide you with the EXACT, COMPLETE context of everything done so far in the project, right from the start to the pause point in Phase 7 Task 2.
>
> Read this document completely to understand the verified architectural state. Do not invent, simplify, reinterpret, or silently "improve" architectural decisions. Trust this document as the absolute source of truth.

> [!WARNING]
> **IMPORTANT — HISTORICAL PHASE NUMBERING DISCLAIMER**
> 
> The authoritative `19_IMPLEMENTATION_MASTER_PLAN.md` defines Phase 6 as **Forensic/Medical Stub Ingestion**, an optional/deferred demo-data task that does **not** block Phase 7.
> 
> Some references to "Phase 6" within this historical handover refer instead to the Database Architecture, Schema, and Security Stabilization work that functionally belongs to Master Plan Phases 2/3. Those references are historical naming carried forward for auditability and must not be interpreted as the canonical Phase 6 definition or as a Phase 7 prerequisite.

---

## 1. PROJECT HISTORY & PRE-PHASE-7 ARCHITECTURE - DEEP DIVE

Civix is a high-security investigative case management platform heavily leveraging graph/ML analytics and synthetic data generation. This section exhaustively documents the decisions made up to this point.

### 1.1 Database-First Architecture & Rigorous Data Integrity
Unlike typical ORM-driven applications, Civix adopts a strict **Database-First** approach. Core domain logic, validation, constraints, and Row-Level Security (RLS) are enforced strictly within PostgreSQL, not just the application layer. This decision guarantees that even if the backend application is compromised or experiences a bug, the data layer prevents unauthorized manipulation or illegal states.

### 1.2 Data Stratification: Operational vs. Analytical
Operational data (`civix` schema) is strongly separated from derived ML graphs and external analytical payloads. Operational tables (such as `civix_user`, `investigative_case`, `person`, `organization`) DO NOT contain target ML labels such as `is_criminal`, `fraud_probability`, or `ground_truth`. This is a deliberate architectural constraint to ensure the operational investigative system mirrors real-world evidence gathering without premature ML taint.

### 1.3 Synthetic Data Strategy
The project incorporates vast synthetic data generation to simulate a global environment for ML testing and UI validation. Synthetic runs are tracked via `generation_run_id` linked across entities. This ensures that synthetic test data can be identified, isolated, and destroyed without polluting potential production data paths.

### 1.4 Epistemic & Assertion Model
The system models facts (assertions) and hypotheses explicitly. The DB records who asserted what, based on which evidence. This allows investigations to track competing theories, unverified claims, and contradictory evidence natively in the schema.

### 1.5 Evidence & Provenance Architecture
Explicit tracking of digital/physical evidence through the `evidence_artifact` and `provenance` tables. Evidence immutability is paramount. The system is designed such that once evidence is logged, it cannot be tampered with. (Note: `chain_of_custody_event` does not exist in the live schema, its duties are handled by the aforementioned tables).

### 1.6 Identity & RLS Architecture
Highly restrictive database access. The API operates as `civix_api` (NOSUPERUSER, NOBYPASSRLS). Each user’s access is strictly isolated using PostgreSQL RLS policies scoped down to individual cases via the `case_access` table.

### 1.7 Security Principles & Connection Pooling
Trust nothing. Identity context must be pushed strictly into the database transaction boundary, preventing connection pool leakage. No "magic" global flags or superuser API access.

---

## 2. EXHAUSTIVE PHASE 6 DATABASE SCHEMA BIBLE

To ensure you have absolute context on the domain modeling, here is the complete Database Schema Bible, which outlines the exact tables, invariants, and foreign key relations constructed up to Phase 6.

<details>
<summary>Click to expand the Complete 03_DATABASE_SCHEMA_BIBLE.md</summary>

# 03 — DATABASE SCHEMA BIBLE
## Every Table, Column, FK, Constraint, and Invariant

**Canonical PostgreSQL schema**: 50 tables.

**Version**: 1.1 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE — UNDER REVISION (Phase 1 Blocker Resolution in progress. BLK-01 through BLK-05 resolved. Patches applied 2026-08-29.)

> [!IMPORTANT]
> This document is the definitive schema contract. No DDL may be written that contradicts this document.
> The existing `database/schema_postgres.sql` is SUPERSEDED and must not be used.
> Record every schema change in `CIVIX_CHANGE_CONTROL.md`.

---

## Schema Namespace

All tables live in the `civix` PostgreSQL schema. No tables in `public`.

```sql
CREATE SCHEMA IF NOT EXISTS civix;
SET search_path TO civix, public;
```

---

## Required Extensions

```sql
CREATE EXTENSION IF NOT EXISTS postgis;          -- Spatial geometry
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;         -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS btree_gist;       -- GIST indexes on non-spatial types (for temporal exclusion)
```

---

## ENUM Types (Migration 02)

```
entity_type_enum:         PERSON, SOURCE_IDENTITY, PHONE_NUMBER, SIM, DEVICE,
                          FINANCIAL_ACCOUNT, VEHICLE, PROPERTY, ORGANIZATION, NETWORK, LOCATION

source_identity_type_enum: NAME, PHONE_MSISDN, IMEI, MAC_ADDRESS, VEHICLE_REG,
                            EMAIL, FACE_EMBEDDING_REF, FINGERPRINT_REF, VOICE_PRINT_REF,
                            AADHAAR_MASKED, PAN_MASKED, DRIVING_LICENSE, PASSPORT_NUMBER, OTHER

predicate_enum:           CALLED, MESSAGED, PINGED_TOWER, USED_DEVICE, USED_SIM,
                          HAD_NUMBER, SEEN_AT, PRESENT_AT, TRANSFERRED_TO, TRANSFERRED_FROM,
                          HOLDS_ACCOUNT, OWNS, OWNED, TRANSFERRED_OWNERSHIP_OF,
                          RECEIVED_PROPERTY, REGISTERED_TO, DRIVER_OF, PASSENGER_IN,
                          MEMBER_OF, EMPLOYED_BY, KNOWN_ASSOCIATE_OF, RESIDED_AT, VISITED,
                          ALIBI_CONFIRMED_AT, DNA_MATCHES, DNA_EXCLUDED,
                          FINGERPRINT_MATCHES, FINGERPRINT_EXCLUDED,
                          FACE_MATCHES, VEHICLE_REG_MATCHES,
                          TIME_OF_DEATH_IS, CAUSE_OF_DEATH_IS, HAS_INJURY,
                          LOCATED_AT, REGISTERED_AT

participant_role_enum:    CALLER, CALLEE, PING_SOURCE, DRIVER, PASSENGER, REGISTERED_OWNER,
                          SENDER, RECEIVER, ACCOUNT_HOLDER, JOINT_HOLDER, BENEFICIARY,
                          PREVIOUS_OWNER, NEW_OWNER, TARGET_PROPERTY, REGISTRAR,
                          LOCATION, CELL_TOWER, VICTIM, SUSPECT, WITNESS, OFFICER,
                          OBSERVER, SUBJECT, COMPLAINANT, SAMPLE_COLLECTOR,
                          EXAMINER, CUSTODIAN, PARTICIPANT

epistemic_status_enum:    POSSIBLE, PROBABLE, CONFIRMED, REFUTED, INCONCLUSIVE

support_stance_enum:      SUPPORT, CONTRADICT, NEUTRAL, INCONCLUSIVE

identity_resolution_status_enum: ACCEPTED, REJECTED, SUPERSEDED, UNRESOLVED, REVIEW_REQUIRED

event_type_enum:          CALL, MESSAGE, TRANSACTION, VEHICLE_SIGHTING, PROPERTY_MUTATION,
                          MEETING, SEIZURE, ARREST, SURVEILLANCE_OBSERVATION,
                          FORENSIC_COLLECTION, MEDICAL_EXAMINATION, FIR_FILING,
                          DEVICE_PING, BORDER_CROSSING, OTHER

case_type_enum:           CRIMINAL, INTELLIGENCE, PROPERTY, FINANCIAL, SURVEILLANCE,
                          FORENSIC, MULTI_CASE

case_status_enum:         OPEN, ACTIVE, SUSPENDED, CLOSED_SOLVED, CLOSED_UNSOLVED, ARCHIVED

case_priority_enum:       CRITICAL, HIGH, MEDIUM, LOW

case_entity_role_enum:    SUSPECT, VICTIM, COMPLAINANT, WITNESS, PERSON_OF_INTEREST,
                          ACCUSED, ACQUITTED, OFFICER_IN_CHARGE, INFORMANT,
                          SUBJECT_ORG, SUBJECT_VEHICLE, SUBJECT_ACCOUNT,
                          SUBJECT_PROPERTY, SUBJECT_DEVICE, RELATED_PERSON

civix_role_enum:          INVESTIGATOR, SUPERVISOR, ANALYST, ADMIN,
                          FORENSIC_EXAMINER, LEGAL_OFFICER, READ_ONLY

clearance_enum:           UNCLASSIFIED, RESTRICTED, CONFIDENTIAL, SECRET

case_permission_enum:     READ, WRITE, ADMIN

audit_action_enum:        LOGIN, LOGOUT, READ, WRITE, EXPORT, RESTRICT,
                          LIFT_RESTRICTION, IDENTITY_RESOLVE, HYPOTHESIS_STATUS_CHANGE,
                          LEAD_DISPOSITION, ADMIN_ACTION, TOMBSTONE_ISSUED

legal_restriction_type_enum: EXPUNGED, SEALED, JUVENILE_PROTECTED, COURT_RESTRICTED,
                              CLASSIFIED, NATIONAL_SECURITY

data_quality_issue_type_enum: IMPOSSIBLE_TIMESTAMP, MALFORMED_RECORD, DUPLICATE_RECORD,
                               MISSING_REQUIRED_FIELD, CONTRADICTORY_DATA, CUSTODY_GAP,
                               UNKNOWN_IDENTIFIER, HASH_MISMATCH, SPATIAL_IMPOSSIBILITY,
                               TEMPORAL_IMPOSSIBILITY, OTHER

location_type_enum:       EXACT_POINT, ESTIMATED_POINT, CELL_SECTOR_POLYGON,
                          CCTV_COVERAGE_POLYGON, PROPERTY_BOUNDARY, CRIME_SCENE,
                          GEOFENCE, ADMIN_BOUNDARY, ROUTE_LINESTRING

hash_algorithm_enum:      SHA256, SHA512, SHA3_256, MD5_DEPRECATED

extraction_type_enum:     FACE_DETECTION, OCR, ANPR, NER, RELATIONSHIP_EXTRACTION,
                          ANOMALY_DETECTION, CLUSTERING, VOICE_PRINT,
                          FINGERPRINT_MATCH, GEOLOCATION_INFERENCE, TEMPORAL_INFERENCE, OTHER

dataset_type_enum:        GOLDEN_WORLD, SYNTHETIC_TRAIN, SYNTHETIC_VAL,
                          SYNTHETIC_TEST, PRODUCTION

## ── BLK-01 RESOLUTION (ADR-012, 2026-08-29) — Five Missing ENUM Types ──────

hypothesis_status_enum:   ACTIVE, UNDER_REVIEW, CONFIRMED, REFUTED, ARCHIVED
  -- ACTIVE: default; under evaluation
  -- UNDER_REVIEW: escalated to supervisor for second opinion
  -- CONFIRMED: human-authorized conclusion (DB CHECK: confirmed_by IS NOT NULL)
  -- REFUTED: definitively disproven by evidence; requires documented basis
  -- ARCHIVED: administratively closed; no conclusion drawn; may be reopened
  -- NOT a status: CLOSED (redundant), PENDING (pre-creation state), PROBABLE (epistemic_status vocab)

lead_priority_enum:       CRITICAL, HIGH, MEDIUM, LOW
  -- Intentionally mirrors case_priority_enum for semantic consistency

lead_status_enum:         OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED
  -- OPEN: created, awaiting assignment (default)
  -- IN_PROGRESS: actively being investigated
  -- CONFIRMED: lead was valid; led to confirmed finding
  -- FALSE_POSITIVE: lead was invalid; required by FL-06 Rekha Verma test
  -- CLOSED: administratively closed without definitive resolution
  -- DEFERRED: postponed; to be reviewed later
  -- Cross-ref: 18_TESTING_VALIDATION_BIBLE.md line 70, 05_EPISTEMIC_MODEL.md line 89

task_type_enum:           INTERVIEW, SURVEILLANCE, SEARCH_AND_SEIZURE, FORENSIC_COLLECTION,
                          FINANCIAL_REVIEW, LEGAL_REQUEST, COURT_ORDER, DATA_ANALYSIS,
                          FIELD_VERIFICATION, OTHER

task_status_enum:         PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED
  -- PENDING: default; task created, not started
  -- COMPLETED: matches completed_at TIMESTAMPTZ column on investigation_task
  -- BLOCKED: cannot proceed; awaiting external dependency
```

---

## Migration 03: Users & Access

### `civix.civix_user`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `user_id` | UUID | NOT NULL | gen_random_uuid() | PK |
| `external_auth_id` | TEXT | NOT NULL | — | UNIQUE. Reference to auth provider. No passwords here. |
| `username` | TEXT | NOT NULL | — | UNIQUE |
| `display_name` | TEXT | NOT NULL | — | |
| `role` | civix_role_enum | NOT NULL | — | |
| `clearance_level` | clearance_enum | NOT NULL | 'UNCLASSIFIED' | |
| `is_active` | BOOL | NOT NULL | TRUE | |
| `department` | TEXT | NULL | — | |
| `created_at` | TIMESTAMPTZ | NOT NULL | now() | |
| `last_login_at` | TIMESTAMPTZ | NULL | — | |

**Invariant**: Authentication secrets (passwords, MFA, tokens) are NEVER stored here. (ADR-010)

---

## Migration 04: Source & Evidence

### `civix.source`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `source_id` | UUID | NOT NULL | gen_random_uuid() | PK |
| `source_name` | TEXT | NOT NULL | — | UNIQUE |
| `agency_type` | TEXT | NOT NULL | — | ENUM: TELECOM, BANK, POLICE, COURT, REVENUE_OFFICE, INFORMANT, CCTV_SYSTEM, HOSPITAL, FORENSIC_LAB, OSINT, OTHER |
| `reliability_score` | DECIMAL(3,2) | NULL | — | CHECK 0.0–1.0 |
| `jurisdiction` | TEXT | NULL | — | |
| `is_identity_protected` | BOOL | NOT NULL | FALSE | TRUE for confidential informants |
| `source_handler_id` | UUID | NULL | — | FK → civix_user. Required if is_identity_protected=TRUE |
| `created_at` | TIMESTAMPTZ | NOT NULL | now() | |

### `civix.source_record`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `source_record_id` | UUID | NOT NULL | gen_random_uuid() | PK |
| `source_id` | UUID | NOT NULL | — | FK → source |
| `external_reference` | TEXT | NULL | — | e.g. CDR-000002 |
| `record_type` | TEXT | NOT NULL | — | CDR_ROW, TRANSACTION_ROW, etc. |
| `raw_content_hash` | BYTEA | NULL | — | SHA-256 of raw record |
| `received_at` | TIMESTAMPTZ | NOT NULL | now() | |
| `superseded_by` | UUID | NULL | — | FK → self. Immutable version chain. |
| `generation_run_id` | UUID | NULL | — | FK → generation_run. Synthetic tag. |

**Invariant**: Never UPDATE a source_record. Corrections insert a new row with superseded_by set.

### `civix.evidence_artifact`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `artifact_id` | UUID | NOT NULL | gen_random_uuid() | PK |
| `sha256_hash` | BYTEA | NOT NULL | — | |
| `hash_algorithm` | hash_algorithm_enum | NOT NULL | 'SHA256' | |
| `file_size_bytes` | BIGINT | NULL | — | |
| `mime_type` | TEXT | NULL | — | |
| `original_filename` | TEXT | NULL | — | |
| `storage_uri` | TEXT | NULL | — | S3/MinIO object key |
| `is_integrity_verified` | BOOL | NOT NULL | FALSE | |
| `acquired_at` | TIMESTAMPTZ | NULL | — | |
| `created_at` | TIMESTAMPTZ | NOT NULL | now() | |

**Constraint**: `UNIQUE(sha256_hash, hash_algorithm)` — composite uniqueness (ADR-004)

### `civix.evidence_instance`
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `instance_id` | UUID | NOT NULL | gen_random_uuid() | PK |
| `artifact_id` | UUID | NOT NULL | — | FK → evidence_artifact |
| `case_id` | UUID | NOT NULL | — | FK → investigative_case. **Critical: resolves GAP-04** |
| `source_record_id` | UUID | NULL | — | FK → source_record |
| `acquired_by` | UUID | NULL | — | FK → civix_user |
| `acquisition_method` | TEXT | NULL | — | e.g. "Telecom Legal Request" |
| `acquisition_context` | TEXT | NULL | — | |
| `legal_status` | TEXT | NOT NULL | 'ACTIVE' | ENUM: ACTIVE, RESTRICTED, SEALED, EXPUNGED |
| `tx_start` | TIMESTAMPTZ | NOT NULL | now() | Bitemporal transaction time start |
| `tx_end` | TIMESTAMPTZ | NULL | — | Bitemporal transaction time end |

---

## Migration 05: Identity

### `civix.entity` — Universal Supertype
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `entity_id` | UUID | NOT NULL | gen_random_uuid() | PK — shared with all subtypes |
| `entity_type` | entity_type_enum | NOT NULL | — | Discriminator column |
| `created_at` | TIMESTAMPTZ | NOT NULL | now() | |
| `created_by` | UUID | NULL | — | FK → civix_user |

**Invariant**: Subtype tables use `entity_id` as both PK and FK to `civix.entity`. No separate surrogate keys.

### `civix.source_identity` — Subtype
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `entity_id` | UUID | NOT NULL | — | PK, FK → entity |
| `raw_identifier` | TEXT | NOT NULL | — | Immutable after creation |
| `identifier_type` | source_identity_type_enum | NOT NULL | — | |
| `source_record_id` | UUID | NULL | — | FK → source_record. Primary provenance anchor for raw-data-derived identities. |
| `observed_at` | TIMESTAMPTZ | NOT NULL | — | Real-world observation time |
| `tx_start` | TIMESTAMPTZ | NOT NULL | now() | |
| `tx_end` | TIMESTAMPTZ | NULL | — | |

**Invariant**: `raw_identifier` is IMMUTABLE. Corrections create a new source_identity row.
**Note**: `UNKNOWN-IMEI` from CDRs becomes `source_identity(identifier_type=IMEI, raw_identifier='UNKNOWN-IMEI')`.

> [!IMPORTANT]
> **BLK-03 RESOLUTION (ADR-014, 2026-08-29)**: `extraction_id` column REMOVED.
> The column `extraction_id UUID NULL FK→extraction` that previously appeared here has been removed.
> **Reason**: Contradicts ADR-006 (provenance via application-enforced type+id, not direct FKs).
> **Replacement**: When a source_identity is AI-derived from an extraction, write to `civix.provenance`:
> `provenance(derived_type='SOURCE_IDENTITY', derived_id=SI.entity_id, source_type='EXTRACTION', source_id=extraction.extraction_id, derivation_method='AI_NER'|'AI_FACE'|'AI_ANPR'|'AI_OTHER')`
> When a source_identity comes from raw data, `source_record_id` is the provenance anchor (no change).

### `civix.person` — Subtype
| Column | Type | Nullable | Default | Notes |
|---|---|---|---|---|
| `entity_id` | UUID | NOT NULL | — | PK, FK → entity |
| `display_name` | TEXT | NOT NULL | — | |
| `date_of_birth` | DATE | NULL | — | |
| `gender` | TEXT | NULL | — | ENUM: MALE, FEMALE, OTHER, UNDISCLOSED |
| `nationality` | CHAR(3) | NULL | — | ISO 3166-1 alpha-3 |
| `is_deceased` | BOOL | NOT NULL | FALSE | |
| `deceased_at` | DATE | NULL | — | |
| `notes` | TEXT | NULL | — | |

**Invariant**: NO `is_criminal`, `is_suspect`, `criminal_record_count`, or similar fields. These are hypotheses. (ADR-005)

### `civix.person_alias`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `alias_id` | UUID PK | NOT NULL | |
| `person_id` | UUID FK→person | NOT NULL | |
| `alias_value` | TEXT | NOT NULL | |
| `alias_type` | TEXT | NOT NULL | AKA, NICKNAME, MAIDEN_NAME, PROFESSIONAL_NAME, ALIAS_CRIMINAL, OTHER |
| `source_record_id` | UUID FK→source_record | NULL | |
| `valid_from` | DATE | NULL | |
| `valid_to` | DATE | NULL | |
| `tx_start` | TIMESTAMPTZ | NOT NULL | |

**Unique**: `UNIQUE(person_id, alias_value, alias_type)`

### `civix.identity_candidate`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `candidate_id` | UUID PK | NOT NULL | |
| `source_identity_id` | UUID FK→source_identity | NOT NULL | |
| `proposed_person_id` | UUID FK→person | NOT NULL | |
| `ai_confidence` | DECIMAL(5,4) | NOT NULL | CHECK 0.0–1.0 |
| `analysis_run_id` | UUID FK→analysis_run | NOT NULL | |
| `is_active` | BOOL | NOT NULL | DEFAULT TRUE |
| `created_at` | TIMESTAMPTZ | NOT NULL | |

**Unique**: `UNIQUE(source_identity_id, proposed_person_id)`
**Note**: Multiple active candidates per source_identity are ALLOWED and expected.

### `civix.identity_resolution`
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `resolution_id` | UUID PK | NOT NULL | |
| `source_identity_id` | UUID FK→source_identity | NOT NULL | |
| `candidate_id` | UUID FK→identity_candidate | NULL | Which candidate was accepted |
| `resolved_person_id` | UUID FK→person | NULL | Null if REJECTED |
| `status` | identity_resolution_status_enum | NOT NULL | |
| `decided_by` | UUID FK→civix_user | NULL | |
| `decision_notes` | TEXT | NULL | |
| `superseded_by` | UUID FK→self | NULL | Self-referential versioning |
| `tx_start` | TIMESTAMPTZ | NOT NULL | |
| `tx_end` | TIMESTAMPTZ | NULL | |

**Constraint**: `CHECK (status != 'ACCEPTED' OR resolved_person_id IS NOT NULL)`
**Invariant**: Never UPDATE. Supersede by inserting new row + setting superseded_by.

### `civix.identity_merge_event` — [Resolves GAP-05]
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `merge_event_id` | UUID PK | NOT NULL | |
| `source_identity_a` | UUID FK→source_identity | NOT NULL | |
| `source_identity_b` | UUID FK→source_identity | NOT NULL | |
| `merged_into_person_id` | UUID FK→person | NOT NULL | |
| `resolution_id` | UUID FK→identity_resolution | NOT NULL | |
| `decided_by` | UUID FK→civix_user | NOT NULL | |
| `occurred_at` | TIMESTAMPTZ | NOT NULL | |
| `reason` | TEXT | NULL | |

**Invariant**: IMMUTABLE. No UPDATE or DELETE.

### `civix.identity_split_event` — [Resolves GAP-05]
| Column | Type | Nullable | Notes |
|---|---|---|---|
| `split_event_id` | UUID PK | NOT NULL | |
| `original_resolution_id` | UUID FK→identity_resolution | NOT NULL | The resolution being overturned |
| `split_source_identity_a` | UUID FK→source_identity | NOT NULL | |
| `split_source_identity_b` | UUID FK→source_identity | NOT NULL | |
| `new_person_b_id` | UUID FK→person | NOT NULL | Newly created canonical person |
| `decided_by` | UUID FK→civix_user | NOT NULL | |
| `reason` | TEXT | NOT NULL | |
| `occurred_at` | TIMESTAMPTZ | NOT NULL | |

---

## Migration 06: Domain Subtypes

### `civix.phone_number`
| `entity_id` UUID PK+FK→entity, `msisdn` VARCHAR(15) UNIQUE NOT NULL, `country_code` CHAR(3) DEFAULT 'IND', `operator` TEXT NULL, `number_type` TEXT NULL |

### `civix.sim`
| `entity_id` UUID PK+FK→entity, `iccid` VARCHAR(22) UNIQUE NOT NULL, `imsi` VARCHAR(15) UNIQUE NULL, `issuing_operator` TEXT NULL |

### `civix.device`
| `entity_id` UUID PK+FK→entity, `imei` VARCHAR(17) UNIQUE NULL, `mac_address` VARCHAR(17) UNIQUE NULL, `device_type` TEXT NOT NULL, `manufacturer` TEXT NULL, `model` TEXT NULL |
**Note**: `imei` is NULLABLE because CDRs may contain UNKNOWN-IMEI (those become source_identity rows, not device rows).

### `civix.vehicle`
| `entity_id` UUID PK+FK→entity, `registration_number` TEXT UNIQUE NOT NULL, `vin` TEXT UNIQUE NULL, `make` TEXT NULL, `model` TEXT NULL, `color` TEXT NULL, `vehicle_type` TEXT NOT NULL, `registration_year` INT NULL |

### `civix.property`
| `entity_id` UUID PK+FK→entity, `property_ref` TEXT NOT NULL, `property_type` TEXT NOT NULL, `area_sqm` DECIMAL NULL, `description` TEXT NULL, `boundary_geometry` GEOMETRY(Polygon, 4326) NULL |

### `civix.financial_account`
| `entity_id` UUID PK+FK→entity, `masked_number` TEXT NOT NULL, `account_type` TEXT NOT NULL, `bank_name` TEXT NULL, `ifsc_code` CHAR(11) NULL, `currency` CHAR(3) DEFAULT 'INR' |
**Note**: Unresolvable account strings (like "Network Beta)" from transactions.csv) become source_identity rows, NOT financial_account rows.

### `civix.organization`
| `entity_id` UUID PK+FK→entity, `legal_name` TEXT NOT NULL, `org_type` TEXT NOT NULL, `registration_number` TEXT NULL, `incorporation_date` DATE NULL, `jurisdiction` TEXT NULL |

### `civix.network`
| `entity_id` UUID PK+FK→entity, `network_name` TEXT NOT NULL, `network_type` TEXT NOT NULL, `notes` TEXT NULL |
**Invariant**: `network_type = 'CRIMINAL'` is investigative categorization, NOT proof of member guilt.

### `civix.location`
| Column | Type | Notes |
|---|---|---|
| `entity_id` | UUID PK+FK→entity | |
| `location_name` | TEXT NULL | |
| `geometry` | GEOMETRY(Geometry, 4326) NOT NULL | Supports Point, Polygon, LineString |
| `location_type` | location_type_enum NOT NULL | |
| `uncertainty_radius_meters` | FLOAT NULL | For estimated points |
| `altitude_meters` | FLOAT NULL | 3D disambiguation |
| `azimuth_degrees` | FLOAT NULL | For cell sector directionality |
| `beamwidth_degrees` | FLOAT NULL | Cell sector angular width |
| `source_record_id` | UUID FK→source_record NULL | |

**Invariant**: Cell tower IDs (CELL-01 through CELL-47) map to `CELL_SECTOR_POLYGON` locations. NEVER store centroid as user position. (ADR-009)

---

## Migration 07: Telecom Relationships

### `civix.sim_number_assignment` — [Resolves GAP-06]
| `assignment_id` UUID PK, `sim_id` UUID FK→sim NOT NULL, `phone_number_id` UUID FK→phone_number NOT NULL, `valid_time` TSTZRANGE NOT NULL, `source_record_id` UUID FK NULL, `tx_start` TIMESTAMPTZ NOT NULL |
**Constraint**: `EXCLUDE USING GIST (phone_number_id WITH =, valid_time WITH &&)` — one MSISDN cannot be assigned to two SIMs simultaneously

### `civix.sim_in_device`
| `id` UUID PK, `sim_id` UUID FK→sim NOT NULL, `device_id` UUID FK→device NOT NULL, `valid_time` TSTZRANGE NOT NULL, `tx_start` TIMESTAMPTZ NOT NULL |
**Constraint**: `EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&)` — physical law: one SIM, one device at a time

---

## Migration 08: Finance

### `civix.account_holder` — [Resolves GAP-07]
| `holder_id` UUID PK, `account_id` UUID FK→financial_account NOT NULL, `holder_entity_id` UUID FK→entity NOT NULL, `holder_role` TEXT NOT NULL (PRIMARY/JOINT/AUTHORIZED_SIGNATORY/POA/NOMINEE/CORPORATE_DIRECTOR), `ownership_percentage` DECIMAL(5,2) NULL CHECK 0–100, `valid_time` TSTZRANGE NOT NULL, `source_record_id` UUID FK NULL, `tx_start` TIMESTAMPTZ NOT NULL |

---

## Migration 09: Cases

### `civix.investigative_case` — [Resolves GAP-02]
| Column | Type | Notes |
|---|---|---|
| `case_id` | UUID PK | |
| `case_number` | TEXT UNIQUE NOT NULL | Format: CIV-2026-001 |
| `title` | TEXT NOT NULL | |
| `case_type` | case_type_enum NOT NULL | |
| `status` | case_status_enum NOT NULL DEFAULT 'OPEN' | |
| `priority` | case_priority_enum NOT NULL DEFAULT 'MEDIUM' | |
| `jurisdiction` | TEXT NOT NULL | |
| `investigating_unit` | TEXT NULL | |
| `opened_at` | DATE NOT NULL | |
| `closed_at` | DATE NULL | |
| `lead_investigator_id` | UUID FK→civix_user NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**Constraint**: `CHECK (closed_at IS NULL OR closed_at >= opened_at)`
**Note**: Physical name is `investigative_case` not `case` to avoid SQL reserved word. (ADR-003)

### `civix.case_entity_role` — [Resolves GAP-08]
| `role_id` UUID PK, `case_id` UUID FK NOT NULL, `entity_id` UUID FK→entity NOT NULL, `role` case_entity_role_enum NOT NULL, `role_basis` TEXT NULL, `assigned_by` UUID FK→civix_user NULL, `valid_from` DATE NULL, `valid_to` DATE NULL |
**Unique**: `UNIQUE(case_id, entity_id, role)`
**Note**: `criminal_history_records.csv` with `P-01: Acquitted` maps to `case_entity_role(role=ACQUITTED)`. NOT a person attribute.

### `civix.fir`
| `fir_id` UUID PK, `case_id` UUID FK NOT NULL, `fir_number` TEXT NOT NULL, `police_station` TEXT NOT NULL, `district` TEXT NOT NULL, `filed_at` TIMESTAMPTZ NOT NULL, `filed_by` UUID FK→civix_user NULL, `complainant_entity_id` UUID FK→entity NULL, `sections_invoked` TEXT[] NULL, `source_record_id` UUID FK NULL |

### `civix.case_access` — [Resolves GAP-09]
| `access_id` UUID PK, `case_id` UUID FK NOT NULL, `user_id` UUID FK NOT NULL, `permission_level` case_permission_enum NOT NULL, `granted_by` UUID FK NOT NULL, `granted_at` TIMESTAMPTZ NOT NULL, `valid_until` TIMESTAMPTZ NULL, `is_revoked` BOOL NOT NULL DEFAULT FALSE, `revoked_by` UUID FK NULL, `revoked_at` TIMESTAMPTZ NULL |
**Unique**: `UNIQUE(case_id, user_id)`
**Purpose**: Foundation for PostgreSQL RLS policies.

### `civix.case_link`
| `link_id` UUID PK, `source_case_id` UUID FK NOT NULL, `target_case_id` UUID FK NOT NULL, `linked_object_type` TEXT NOT NULL, `linked_object_id` UUID NOT NULL, `share_scope` TEXT NOT NULL, `authorized_by` UUID FK NOT NULL, `created_at` TIMESTAMPTZ NOT NULL |
**Constraint**: `CHECK (source_case_id != target_case_id)`

---

## Migration 10: Epistemic Pipeline

### `civix.analysis_run`
| `run_id` UUID PK, `model_name` TEXT NOT NULL, `model_version` TEXT NOT NULL, `algorithm_type` TEXT NOT NULL, `algorithm_parameters` JSONB NULL, `input_snapshot_hash` BYTEA NULL, `input_snapshot_tx_time` TIMESTAMPTZ NULL, `started_at` TIMESTAMPTZ NOT NULL, `finished_at` TIMESTAMPTZ NULL, `initiated_by` UUID FK NULL, `generation_run_id` UUID FK NULL |

### `civix.observation`
| `observation_id` UUID PK, `instance_id` UUID FK→evidence_instance NOT NULL, `observer_type` TEXT NOT NULL, `observed_by` UUID FK→civix_user NULL, `observation_type` TEXT NULL, `observation_text` TEXT NULL, `structured_content` JSONB NULL, `observed_at` TIMESTAMPTZ NOT NULL, `tx_start` TIMESTAMPTZ NOT NULL |
**Invariant**: IMMUTABLE. Corrections create new rows.

### `civix.extraction`
| `extraction_id` UUID PK, `instance_id` UUID FK NOT NULL, `analysis_run_id` UUID FK NOT NULL, `extraction_type` extraction_type_enum NOT NULL, `extracted_value` JSONB NOT NULL, `ai_confidence` DECIMAL(5,4) NOT NULL CHECK 0.0–1.0, `is_superseded` BOOL NOT NULL DEFAULT FALSE, `superseded_by` UUID FK→self NULL, `tx_start` TIMESTAMPTZ NOT NULL |

### `civix.event`
| Column | Type | Notes |
|---|---|---|
| `event_id` | UUID PK | |
| `event_type` | event_type_enum NOT NULL | |
| `occurred_at` | TSTZRANGE NOT NULL | Real-world time interval (not scalar — uncertainty supported) |
| `description` | TEXT NULL | |
| `source_record_id` | UUID FK NULL | |
| `tx_start` | TIMESTAMPTZ NOT NULL | System ingestion time |
| `generation_run_id` | UUID FK NULL | |

**No entity FKs on event**: Location is an `event_participant(role=LOCATION)`. (ADR-021, see `05_EPISTEMIC_MODEL.md`)

### `civix.event_participant`
| `participant_id` UUID PK, `event_id` UUID FK NOT NULL, `entity_id` UUID FK→entity NOT NULL, `participant_role` participant_role_enum NOT NULL, `role_confidence` DECIMAL(5,4) NULL, `tx_start` TIMESTAMPTZ NOT NULL |
**Unique**: `UNIQUE(event_id, entity_id, participant_role)`
**Note**: NO `valid_from/valid_to` on this table. Temporal ownership lives in `assertion` and `account_holder`.

### `civix.assertion`
| Column | Type | Notes |
|---|---|---|
| `assertion_id` | UUID PK | |
| `subject_entity_id` | UUID FK→entity NOT NULL | |
| `predicate` | predicate_enum NOT NULL | CONTROLLED VOCABULARY ONLY |
| `object_entity_id` | UUID FK→entity NULL | For entity-entity assertions |
| `object_value` | TEXT NULL | For scalar assertions |
| `object_location_id` | UUID FK→location NULL | For spatial assertions |
| `epistemic_status` | epistemic_status_enum NOT NULL | Belief in the S-P-O claim itself |
| `ai_confidence` | DECIMAL(5,4) NULL | CHECK 0.0–1.0 |
| `asserted_by` | UUID FK→civix_user NULL | Human assertor |
| `source_analysis_run_id` | UUID FK→analysis_run NULL | AI assertor |
| `valid_from` | TIMESTAMPTZ NULL | Real-world validity start |
| `valid_to` | TIMESTAMPTZ NULL | Real-world validity end |
| `tx_start` | TIMESTAMPTZ NOT NULL | |
| `tx_end` | TIMESTAMPTZ NULL | |
| `generation_run_id` | UUID FK NULL | |

**Constraints**:
- `CHECK (object_entity_id IS NOT NULL OR object_value IS NOT NULL OR object_location_id IS NOT NULL)`
- `CHECK (asserted_by IS NOT NULL OR source_analysis_run_id IS NOT NULL)`
- `CHECK (ai_confidence IS NULL OR ai_confidence BETWEEN 0.0 AND 1.0)`

**Invariant**: Assertion has NO stance. Stance belongs in hypothesis_support. (ADR-002)
**Invariant**: `predicate` MUST come from `predicate_enum`. Free-text predicates are BANNED.

### `civix.hypothesis`
| `hypothesis_id` UUID PK, `case_id` UUID FK NOT NULL, `hypothesis_text` TEXT NOT NULL, `status` hypothesis_status_enum NOT NULL DEFAULT 'ACTIVE', `created_by` UUID FK NOT NULL, `confirmed_by` UUID FK NULL, `tx_start` TIMESTAMPTZ NOT NULL, `tx_end` TIMESTAMPTZ NULL |
**Constraint**: `CHECK (status != 'CONFIRMED' OR confirmed_by IS NOT NULL)` — AI cannot self-confirm hypotheses.

### `civix.hypothesis_support`
| `support_id` UUID PK, `hypothesis_id` UUID FK NOT NULL, `assertion_id` UUID FK NOT NULL, `stance` support_stance_enum NOT NULL, `weight` DECIMAL(5,4) NOT NULL DEFAULT 1.0, `assigned_by` UUID FK NULL, `analysis_run_id` UUID FK NULL, `tx_start` TIMESTAMPTZ NOT NULL |
**Unique**: `UNIQUE(hypothesis_id, assertion_id)`

---

## Migration 11: Workflow

### `civix.investigative_lead`
| `lead_id` UUID PK, `case_id` UUID FK NOT NULL, `generated_by_run_id` UUID FK NULL, `generated_by_person` UUID FK NULL, `lead_text` TEXT NOT NULL, `explanation` TEXT NULL, `priority` lead_priority_enum NOT NULL DEFAULT 'MEDIUM', `status` lead_status_enum NOT NULL DEFAULT 'OPEN', `ai_confidence` DECIMAL(5,4) NULL, `created_at` TIMESTAMPTZ NOT NULL, `disposition_notes` TEXT NULL, `disposed_by` UUID FK NULL, `disposed_at` TIMESTAMPTZ NULL |
**Constraint**: `CHECK (generated_by_run_id IS NOT NULL OR generated_by_person IS NOT NULL)`

### `civix.investigation_task`
| `task_id` UUID PK, `lead_id` UUID FK NULL, `case_id` UUID FK NOT NULL, `task_type` task_type_enum NOT NULL, `assigned_to` UUID FK NULL, `status` task_status_enum NOT NULL DEFAULT 'PENDING', `due_date` DATE NULL, `outcome_notes` TEXT NULL, `created_at` TIMESTAMPTZ NOT NULL, `completed_at` TIMESTAMPTZ NULL |

---

## Migration 12: Forensic Stubs (Phase 2 Extensibility)

### `civix.forensic_report` (MVP stub)
| `report_id` UUID PK, `instance_id` UUID FK NOT NULL, `report_type` TEXT NOT NULL, `lab_name` TEXT NULL, `examiner_name` TEXT NULL, `findings_summary` TEXT NULL |

### `civix.medical_report` (MVP stub)
| `report_id` UUID PK, `instance_id` UUID FK NOT NULL, `examination_type` TEXT NOT NULL, `findings_summary` TEXT NULL, `practitioner_name` TEXT NULL, `examination_date` DATE NULL |

**Phase 2 tables** (architectured, not yet implemented): `forensic_sample`, `chain_of_custody_event`, `lab_examination`, `lab_result`, `reference_profile`, `comparison`, `forensic_finding`, `medical_examination`, `medical_finding`, `autopsy`, `toxicology_result`

---

## Migration 13: Security & Legal

### `civix.legal_restriction`
| `restriction_id` UUID PK, `target_entity_id` UUID FK→entity NULL, `target_artifact_id` UUID FK→evidence_artifact NULL, `restriction_type` legal_restriction_type_enum NOT NULL, `authority` TEXT NOT NULL, `court_order_reference` TEXT NULL, `effective_range` TSTZRANGE NOT NULL, `scope` TEXT NOT NULL, `status` TEXT NOT NULL DEFAULT 'ACTIVE', `created_by` UUID FK NOT NULL, `lifted_by` UUID FK NULL, `lifted_at` TIMESTAMPTZ NULL |
**Constraint**: `CHECK (target_entity_id IS NOT NULL OR target_artifact_id IS NOT NULL)`
**Phase 6 Status**: `legal_restriction` is structurally modeled, but global-entity filtering for EXPUNGED/SEALED records is deferred to the Phase 8/9 authorization layer. Phase 6 RLS remains responsible for case isolation. No application endpoint may expose restricted records once authorization enforcement is implemented.

### `civix.audit_event`
| `audit_id` UUID PK, `user_id` UUID FK NOT NULL, `action` audit_action_enum NOT NULL, `target_table` TEXT NOT NULL, `target_id` UUID NOT NULL, `case_context_id` UUID FK NULL, `ip_address` INET NULL, `timestamp` TIMESTAMPTZ NOT NULL, `metadata` JSONB NULL |
**Invariant**: APPEND-ONLY. Trigger prevents UPDATE or DELETE.

### `civix.outbox` — [Resolves GAP-25]
| `id` UUID PK, `entity_id` UUID NOT NULL, `action` TEXT NOT NULL (UPSERT/DELETE/TOMBSTONE), `entity_type` TEXT NOT NULL, `payload` JSONB NOT NULL, `created_at` TIMESTAMPTZ NOT NULL, `consumed_at` TIMESTAMPTZ NULL |
**Purpose**: Only mechanism for Neo4j synchronization. (ADR-008)

---

## Migration 14: Provenance & Data Quality

### `civix.provenance`
| `provenance_id` UUID PK, `derived_type` TEXT NOT NULL, `derived_id` UUID NOT NULL, `source_type` TEXT NOT NULL, `source_id` UUID NOT NULL, `derivation_method` TEXT NOT NULL, `created_at` TIMESTAMPTZ NOT NULL |
**Note**: `derived_id` and `source_id` are NOT database-level FKs (see ADR-006). Integrity enforced at application layer.

### `civix.data_quality_issue` — [Resolves GAP-03]
| `issue_id` UUID PK, `affected_entity_type` TEXT NOT NULL, `affected_entity_id` UUID NOT NULL, `issue_type` data_quality_issue_type_enum NOT NULL, `severity` TEXT NOT NULL (CRITICAL/HIGH/MEDIUM/LOW/INFO), `detected_by` TEXT NOT NULL, `detection_run_id` UUID FK NULL, `detected_at` TIMESTAMPTZ NOT NULL, `description` TEXT NOT NULL, `status` TEXT NOT NULL DEFAULT 'OPEN', `resolution_notes` TEXT NULL, `resolved_by` UUID FK NULL, `resolved_at` TIMESTAMPTZ NULL |

---

## Migration 15: Synthetic Data Control

### `civix.dataset`
| `dataset_id` UUID PK, `name` TEXT UNIQUE, `dataset_type` dataset_type_enum, `version` TEXT, `is_production_isolated` BOOL DEFAULT TRUE |

### `civix.scenario`
| `scenario_id` UUID PK, `dataset_id` UUID FK, `scenario_label` TEXT, `random_seed` BIGINT, `ground_truth` JSONB |
**Invariant**: `ground_truth` JSONB is NEVER projected to Neo4j and NEVER included in ML feature extraction.

### `civix.generation_run`
| `run_id` UUID PK, `scenario_id` UUID FK, `generator_version` TEXT, `started_at` TIMESTAMPTZ, `record_counts` JSONB |
**Usage**: All synthetic rows in operational tables have `generation_run_id FK`. ML pipelines filter `WHERE generation_run_id IS NULL`.

---

## Architecture Invariants (From Hardening Report)

See `21_KNOWN_GAPS_AND_RISKS.md` for the full invariant register (INV-01 through INV-20).

Key invariants for DDL implementors:
- INV-01: Assertion has no stance
- INV-03: SourceIdentity.raw_identifier is immutable
- INV-04: EvidenceArtifact uniqueness = (sha256_hash, hash_algorithm)
- INV-05: One event may target many entities (no entity FKs on event)
- INV-08: AI cannot autonomously confirm a hypothesis (DB CHECK constraint)
- INV-13: audit_event is append-only (DB trigger)
- INV-14: Synthetic ground_truth never projected to Neo4j
- INV-17: is_criminal must not exist on Person
- INV-18: Free-text predicates are banned
- INV-19: Cell tower centroid ≠ user location
- INV-20: Outbox is the only Neo4j sync mechanism

</details>

---

## 3. EXHAUSTIVE PHASE 6 DATABASE RAW SQL SCHEMA DUMP

To ensure you have the exact, irrefutable live database state, here is the full pg_dump of the `civix` schema running on PostgreSQL 16 on port 5433. Do NOT make DDL assumptions; read the actual schema definition below.

<details>
<summary>Click to expand the FULL PostgreSQL 16 Schema Dump</summary>

```sql
--
-- PostgreSQL database dump
--

\restrict FgQE42Hro7qKrrXldpeaKzeB53pcav9hX2jW2KdkTx6ZhKuGPxs9PhXzRWfZkFV

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: civix; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA civix;


ALTER SCHEMA civix OWNER TO postgres;

--
-- Name: audit_action_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.audit_action_enum AS ENUM (
    'LOGIN',
    'LOGOUT',
    'READ',
    'WRITE',
    'EXPORT',
    'RESTRICT',
    'LIFT_RESTRICTION',
    'IDENTITY_RESOLVE',
    'HYPOTHESIS_STATUS_CHANGE',
    'LEAD_DISPOSITION',
    'ADMIN_ACTION',
    'TOMBSTONE_ISSUED'
);


ALTER TYPE civix.audit_action_enum OWNER TO postgres;

--
-- Name: case_entity_role_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_entity_role_enum AS ENUM (
    'SUSPECT',
    'VICTIM',
    'COMPLAINANT',
    'WITNESS',
    'PERSON_OF_INTEREST',
    'ACCUSED',
    'ACQUITTED',
    'OFFICER_IN_CHARGE',
    'INFORMANT',
    'SUBJECT_ORG',
    'SUBJECT_VEHICLE',
    'SUBJECT_ACCOUNT',
    'SUBJECT_PROPERTY',
    'SUBJECT_DEVICE',
    'RELATED_PERSON'
);


ALTER TYPE civix.case_entity_role_enum OWNER TO postgres;

--
-- Name: case_permission_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_permission_enum AS ENUM (
    'READ',
    'WRITE',
    'ADMIN'
);


ALTER TYPE civix.case_permission_enum OWNER TO postgres;

--
-- Name: case_priority_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_priority_enum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE civix.case_priority_enum OWNER TO postgres;

--
-- Name: case_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_status_enum AS ENUM (
    'OPEN',
    'ACTIVE',
    'SUSPENDED',
    'CLOSED_SOLVED',
    'CLOSED_UNSOLVED',
    'ARCHIVED'
);


ALTER TYPE civix.case_status_enum OWNER TO postgres;

--
-- Name: case_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_type_enum AS ENUM (
    'CRIMINAL',
    'INTELLIGENCE',
    'PROPERTY',
    'FINANCIAL',
    'SURVEILLANCE',
    'FORENSIC',
    'MULTI_CASE'
);


ALTER TYPE civix.case_type_enum OWNER TO postgres;

--
-- Name: civix_role_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.civix_role_enum AS ENUM (
    'INVESTIGATOR',
    'SUPERVISOR',
    'ANALYST',
    'ADMIN',
    'FORENSIC_EXAMINER',
    'LEGAL_OFFICER',
    'READ_ONLY'
);


ALTER TYPE civix.civix_role_enum OWNER TO postgres;

--
-- Name: clearance_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.clearance_enum AS ENUM (
    'UNCLASSIFIED',
    'RESTRICTED',
    'CONFIDENTIAL',
    'SECRET'
);


ALTER TYPE civix.clearance_enum OWNER TO postgres;

--
-- Name: data_quality_issue_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.data_quality_issue_type_enum AS ENUM (
    'IMPOSSIBLE_TIMESTAMP',
    'MALFORMED_RECORD',
    'DUPLICATE_RECORD',
    'MISSING_REQUIRED_FIELD',
    'CONTRADICTORY_DATA',
    'CUSTODY_GAP',
    'UNKNOWN_IDENTIFIER',
    'HASH_MISMATCH',
    'SPATIAL_IMPOSSIBILITY',
    'TEMPORAL_IMPOSSIBILITY',
    'OTHER'
);


ALTER TYPE civix.data_quality_issue_type_enum OWNER TO postgres;

--
-- Name: dataset_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.dataset_type_enum AS ENUM (
    'GOLDEN_WORLD',
    'SYNTHETIC_TRAIN',
    'SYNTHETIC_VAL',
    'SYNTHETIC_TEST',
    'PRODUCTION'
);


ALTER TYPE civix.dataset_type_enum OWNER TO postgres;

--
-- Name: entity_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.entity_type_enum AS ENUM (
    'PERSON',
    'SOURCE_IDENTITY',
    'PHONE_NUMBER',
    'SIM',
    'DEVICE',
    'FINANCIAL_ACCOUNT',
    'VEHICLE',
    'PROPERTY',
    'ORGANIZATION',
    'NETWORK',
    'LOCATION'
);


ALTER TYPE civix.entity_type_enum OWNER TO postgres;

--
-- Name: epistemic_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.epistemic_status_enum AS ENUM (
    'POSSIBLE',
    'PROBABLE',
    'CONFIRMED',
    'REFUTED',
    'INCONCLUSIVE'
);


ALTER TYPE civix.epistemic_status_enum OWNER TO postgres;

--
-- Name: event_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.event_type_enum AS ENUM (
    'CALL',
    'MESSAGE',
    'TRANSACTION',
    'VEHICLE_SIGHTING',
    'PROPERTY_MUTATION',
    'MEETING',
    'SEIZURE',
    'ARREST',
    'SURVEILLANCE_OBSERVATION',
    'FORENSIC_COLLECTION',
    'MEDICAL_EXAMINATION',
    'FIR_FILING',
    'DEVICE_PING',
    'BORDER_CROSSING',
    'OTHER'
);


ALTER TYPE civix.event_type_enum OWNER TO postgres;

--
-- Name: extraction_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.extraction_type_enum AS ENUM (
    'FACE_DETECTION',
    'OCR',
    'ANPR',
    'NER',
    'RELATIONSHIP_EXTRACTION',
    'ANOMALY_DETECTION',
    'CLUSTERING',
    'VOICE_PRINT',
    'FINGERPRINT_MATCH',
    'GEOLOCATION_INFERENCE',
    'TEMPORAL_INFERENCE',
    'OTHER'
);


ALTER TYPE civix.extraction_type_enum OWNER TO postgres;

--
-- Name: hash_algorithm_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.hash_algorithm_enum AS ENUM (
    'SHA256',
    'SHA512',
    'SHA3_256',
    'MD5_DEPRECATED'
);


ALTER TYPE civix.hash_algorithm_enum OWNER TO postgres;

--
-- Name: hypothesis_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.hypothesis_status_enum AS ENUM (
    'ACTIVE',
    'UNDER_REVIEW',
    'CONFIRMED',
    'REFUTED',
    'ARCHIVED'
);


ALTER TYPE civix.hypothesis_status_enum OWNER TO postgres;

--
-- Name: identity_resolution_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.identity_resolution_status_enum AS ENUM (
    'ACCEPTED',
    'REJECTED',
    'SUPERSEDED',
    'UNRESOLVED',
    'REVIEW_REQUIRED'
);


ALTER TYPE civix.identity_resolution_status_enum OWNER TO postgres;

--
-- Name: lead_priority_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.lead_priority_enum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE civix.lead_priority_enum OWNER TO postgres;

--
-- Name: lead_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.lead_status_enum AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'CONFIRMED',
    'FALSE_POSITIVE',
    'CLOSED',
    'DEFERRED'
);


ALTER TYPE civix.lead_status_enum OWNER TO postgres;

--
-- Name: legal_restriction_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.legal_restriction_type_enum AS ENUM (
    'EXPUNGED',
    'SEALED',
    'JUVENILE_PROTECTED',
    'COURT_RESTRICTED',
    'CLASSIFIED',
    'NATIONAL_SECURITY'
);


ALTER TYPE civix.legal_restriction_type_enum OWNER TO postgres;

--
-- Name: location_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.location_type_enum AS ENUM (
    'EXACT_POINT',
    'ESTIMATED_POINT',
    'CELL_SECTOR_POLYGON',
    'CCTV_COVERAGE_POLYGON',
    'PROPERTY_BOUNDARY',
    'CRIME_SCENE',
    'GEOFENCE',
    'ADMIN_BOUNDARY',
    'ROUTE_LINESTRING'
);


ALTER TYPE civix.location_type_enum OWNER TO postgres;

--
-- Name: participant_role_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.participant_role_enum AS ENUM (
    'CALLER',
    'CALLEE',
    'PING_SOURCE',
    'DRIVER',
    'PASSENGER',
    'REGISTERED_OWNER',
    'SENDER',
    'RECEIVER',
    'ACCOUNT_HOLDER',
    'JOINT_HOLDER',
    'BENEFICIARY',
    'PREVIOUS_OWNER',
    'NEW_OWNER',
    'TARGET_PROPERTY',
    'REGISTRAR',
    'LOCATION',
    'CELL_TOWER',
    'VICTIM',
    'SUSPECT',
    'WITNESS',
    'OFFICER',
    'OBSERVER',
    'SUBJECT',
    'COMPLAINANT',
    'SAMPLE_COLLECTOR',
    'EXAMINER',
    'CUSTODIAN',
    'PARTICIPANT'
);


ALTER TYPE civix.participant_role_enum OWNER TO postgres;

--
-- Name: predicate_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.predicate_enum AS ENUM (
    'CALLED',
    'MESSAGED',
    'PINGED_TOWER',
    'USED_DEVICE',
    'USED_SIM',
    'HAD_NUMBER',
    'SEEN_AT',
    'PRESENT_AT',
    'TRANSFERRED_TO',
    'TRANSFERRED_FROM',
    'HOLDS_ACCOUNT',
    'OWNS',
    'OWNED',
    'TRANSFERRED_OWNERSHIP_OF',
    'RECEIVED_PROPERTY',
    'REGISTERED_TO',
    'DRIVER_OF',
    'PASSENGER_IN',
    'MEMBER_OF',
    'EMPLOYED_BY',
    'KNOWN_ASSOCIATE_OF',
    'RESIDED_AT',
    'VISITED',
    'ALIBI_CONFIRMED_AT',
    'DNA_MATCHES',
    'DNA_EXCLUDED',
    'FINGERPRINT_MATCHES',
    'FINGERPRINT_EXCLUDED',
    'FACE_MATCHES',
    'VEHICLE_REG_MATCHES',
    'TIME_OF_DEATH_IS',
    'CAUSE_OF_DEATH_IS',
    'HAS_INJURY',
    'LOCATED_AT',
    'REGISTERED_AT'
);


ALTER TYPE civix.predicate_enum OWNER TO postgres;

--
-- Name: source_identity_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.source_identity_type_enum AS ENUM (
    'NAME',
    'PHONE_MSISDN',
    'IMEI',
    'MAC_ADDRESS',
    'VEHICLE_REG',
    'EMAIL',
    'FACE_EMBEDDING_REF',
    'FINGERPRINT_REF',
    'VOICE_PRINT_REF',
    'AADHAAR_MASKED',
    'PAN_MASKED',
    'DRIVING_LICENSE',
    'PASSPORT_NUMBER',
    'OTHER'
);


ALTER TYPE civix.source_identity_type_enum OWNER TO postgres;

--
-- Name: support_stance_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.support_stance_enum AS ENUM (
    'SUPPORT',
    'CONTRADICT',
    'NEUTRAL',
    'INCONCLUSIVE'
);


ALTER TYPE civix.support_stance_enum OWNER TO postgres;

--
-- Name: task_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.task_status_enum AS ENUM (
    'PENDING',
    'ASSIGNED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED',
    'BLOCKED'
);


ALTER TYPE civix.task_status_enum OWNER TO postgres;

--
-- Name: task_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.task_type_enum AS ENUM (
    'INTERVIEW',
    'SURVEILLANCE',
    'SEARCH_AND_SEIZURE',
    'FORENSIC_COLLECTION',
    'FINANCIAL_REVIEW',
    'LEGAL_REQUEST',
    'COURT_ORDER',
    'DATA_ANALYSIS',
    'FIELD_VERIFICATION',
    'OTHER'
);


ALTER TYPE civix.task_type_enum OWNER TO postgres;

--
-- Name: block_mutation(); Type: FUNCTION; Schema: civix; Owner: postgres
--

CREATE FUNCTION civix.block_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RAISE EXCEPTION 'Updates and deletions are strictly forbidden on this immutable audit table.';
    END;
    $$;


ALTER FUNCTION civix.block_mutation() OWNER TO postgres;

--
-- Name: block_operational_delete(); Type: FUNCTION; Schema: civix; Owner: postgres
--

CREATE FUNCTION civix.block_operational_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF OLD.generation_run_id IS NULL THEN
            RAISE EXCEPTION 'Operational deletion of non-synthetic records is strictly forbidden.';
        END IF;
        RETURN OLD;
    END;
    $$;


ALTER FUNCTION civix.block_operational_delete() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account_holder; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.account_holder (
    holder_id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid NOT NULL,
    holder_entity_id uuid NOT NULL,
    holder_role text NOT NULL,
    ownership_percentage numeric(5,2),
    valid_time tstzrange NOT NULL,
    source_record_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT check_ownership_percentage CHECK (((ownership_percentage >= (0)::numeric) AND (ownership_percentage <= (100)::numeric)))
);


ALTER TABLE civix.account_holder OWNER TO postgres;

--
-- Name: analysis_run; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.analysis_run (
    run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    model_name text NOT NULL,
    model_version text NOT NULL,
    algorithm_type text NOT NULL,
    algorithm_parameters jsonb,
    input_snapshot_hash bytea,
    input_snapshot_tx_time timestamp with time zone,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone,
    initiated_by uuid,
    generation_run_id uuid
);


ALTER TABLE civix.analysis_run OWNER TO postgres;

--
-- Name: assertion; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.assertion (
    assertion_id uuid DEFAULT gen_random_uuid() NOT NULL,
    subject_entity_id uuid NOT NULL,
    predicate civix.predicate_enum NOT NULL,
    object_entity_id uuid,
    object_value text,
    object_location_id uuid,
    epistemic_status civix.epistemic_status_enum NOT NULL,
    ai_confidence numeric(5,4),
    asserted_by uuid,
    source_analysis_run_id uuid,
    valid_from timestamp with time zone,
    valid_to timestamp with time zone,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_assertion_confidence CHECK (((ai_confidence IS NULL) OR ((ai_confidence >= (0)::numeric) AND (ai_confidence <= (1)::numeric)))),
    CONSTRAINT chk_assertion_object CHECK (((object_entity_id IS NOT NULL) OR (object_value IS NOT NULL) OR (object_location_id IS NOT NULL))),
    CONSTRAINT chk_assertion_source CHECK (((asserted_by IS NOT NULL) OR (source_analysis_run_id IS NOT NULL)))
);


ALTER TABLE civix.assertion OWNER TO postgres;

--
-- Name: audit_event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.audit_event (
    audit_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    action civix.audit_action_enum NOT NULL,
    target_table text NOT NULL,
    target_id uuid NOT NULL,
    case_context_id uuid,
    ip_address inet,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    metadata jsonb
);


ALTER TABLE civix.audit_event OWNER TO postgres;

--
-- Name: case_access; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.case_access (
    access_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    user_id uuid NOT NULL,
    permission_level civix.case_permission_enum NOT NULL,
    granted_by uuid NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    valid_until timestamp with time zone,
    is_revoked boolean DEFAULT false NOT NULL,
    revoked_by uuid,
    revoked_at timestamp with time zone
);


ALTER TABLE civix.case_access OWNER TO postgres;

--
-- Name: case_entity_role; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.case_entity_role (
    role_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    entity_id uuid NOT NULL,
    role civix.case_entity_role_enum NOT NULL,
    role_basis text,
    assigned_by uuid,
    valid_from date,
    valid_to date,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.case_entity_role FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.case_entity_role OWNER TO postgres;

--
-- Name: case_link; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.case_link (
    link_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_case_id uuid NOT NULL,
    target_case_id uuid NOT NULL,
    linked_object_type text NOT NULL,
    linked_object_id uuid NOT NULL,
    share_scope text NOT NULL,
    authorized_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT chk_case_link_not_self CHECK ((source_case_id <> target_case_id))
);

ALTER TABLE ONLY civix.case_link FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.case_link OWNER TO postgres;

--
-- Name: civix_user; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.civix_user (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    external_auth_id text NOT NULL,
    username text NOT NULL,
    display_name text NOT NULL,
    role civix.civix_role_enum NOT NULL,
    clearance_level civix.clearance_enum DEFAULT 'UNCLASSIFIED'::civix.clearance_enum NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    department text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone
);


ALTER TABLE civix.civix_user OWNER TO postgres;

--
-- Name: data_quality_issue; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.data_quality_issue (
    issue_id uuid DEFAULT gen_random_uuid() NOT NULL,
    affected_entity_type text NOT NULL,
    affected_entity_id uuid NOT NULL,
    issue_type civix.data_quality_issue_type_enum NOT NULL,
    severity text NOT NULL,
    detected_by text NOT NULL,
    detection_run_id uuid,
    detected_at timestamp with time zone DEFAULT now() NOT NULL,
    description text NOT NULL,
    status text DEFAULT 'OPEN'::text NOT NULL,
    resolution_notes text,
    resolved_by uuid,
    resolved_at timestamp with time zone
);


ALTER TABLE civix.data_quality_issue OWNER TO postgres;

--
-- Name: dataset; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.dataset (
    dataset_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    dataset_type civix.dataset_type_enum NOT NULL
);


ALTER TABLE civix.dataset OWNER TO postgres;

--
-- Name: device; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.device (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'DEVICE'::civix.entity_type_enum NOT NULL,
    imei character varying(17),
    mac_address character varying(17),
    device_type text NOT NULL,
    manufacturer text,
    model text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_device CHECK ((entity_type = 'DEVICE'::civix.entity_type_enum))
);


ALTER TABLE civix.device OWNER TO postgres;

--
-- Name: entity; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.entity (
    entity_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type civix.entity_type_enum NOT NULL,
    generation_run_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid
);


ALTER TABLE civix.entity OWNER TO postgres;

--
-- Name: event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.event (
    event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_type civix.event_type_enum NOT NULL,
    occurred_at tstzrange NOT NULL,
    description text,
    source_record_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.event OWNER TO postgres;

--
-- Name: event_participant; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.event_participant (
    participant_id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_id uuid NOT NULL,
    entity_id uuid NOT NULL,
    participant_role civix.participant_role_enum NOT NULL,
    role_confidence numeric(5,4),
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.event_participant OWNER TO postgres;

--
-- Name: evidence_artifact; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.evidence_artifact (
    artifact_id uuid DEFAULT gen_random_uuid() NOT NULL,
    sha256_hash bytea NOT NULL,
    hash_algorithm civix.hash_algorithm_enum DEFAULT 'SHA256'::civix.hash_algorithm_enum NOT NULL,
    file_size_bytes bigint,
    mime_type text,
    original_filename text,
    storage_uri text,
    is_integrity_verified boolean DEFAULT false NOT NULL,
    acquired_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.evidence_artifact OWNER TO postgres;

--
-- Name: evidence_instance; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.evidence_instance (
    instance_id uuid DEFAULT gen_random_uuid() NOT NULL,
    artifact_id uuid NOT NULL,
    case_id uuid NOT NULL,
    source_record_id uuid,
    acquired_by uuid,
    acquisition_method text,
    acquisition_context text,
    legal_status text DEFAULT 'ACTIVE'::text NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.evidence_instance FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.evidence_instance OWNER TO postgres;

--
-- Name: extraction; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.extraction (
    extraction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    analysis_run_id uuid NOT NULL,
    extraction_type civix.extraction_type_enum NOT NULL,
    extracted_value jsonb NOT NULL,
    ai_confidence numeric(5,4) NOT NULL,
    is_superseded boolean DEFAULT false NOT NULL,
    superseded_by uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT chk_ai_confidence_ext CHECK (((ai_confidence >= (0)::numeric) AND (ai_confidence <= (1)::numeric)))
);

ALTER TABLE ONLY civix.extraction FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.extraction OWNER TO postgres;

--
-- Name: financial_account; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.financial_account (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'FINANCIAL_ACCOUNT'::civix.entity_type_enum NOT NULL,
    masked_number text NOT NULL,
    account_type text NOT NULL,
    bank_name text,
    ifsc_code character varying(11),
    currency character varying(3) DEFAULT 'INR'::character varying,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_financial_account CHECK ((entity_type = 'FINANCIAL_ACCOUNT'::civix.entity_type_enum))
);


ALTER TABLE civix.financial_account OWNER TO postgres;

--
-- Name: fir; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.fir (
    fir_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    fir_number text NOT NULL,
    police_station text NOT NULL,
    district text NOT NULL,
    filed_at timestamp with time zone NOT NULL,
    filed_by uuid,
    complainant_entity_id uuid,
    sections_invoked text[],
    source_record_id uuid,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.fir FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.fir OWNER TO postgres;

--
-- Name: forensic_report; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.forensic_report (
    report_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    report_type text NOT NULL,
    lab_name text,
    examiner_name text,
    findings_summary text,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.forensic_report FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.forensic_report OWNER TO postgres;

--
-- Name: generation_run; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.generation_run (
    generation_run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    dataset_id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    run_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    world_seed bigint,
    generator_version text
);


ALTER TABLE civix.generation_run OWNER TO postgres;

--
-- Name: hypothesis; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.hypothesis (
    hypothesis_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    hypothesis_text text NOT NULL,
    status civix.hypothesis_status_enum DEFAULT 'ACTIVE'::civix.hypothesis_status_enum NOT NULL,
    created_by uuid NOT NULL,
    confirmed_by uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_hypothesis_status CHECK (((status <> 'CONFIRMED'::civix.hypothesis_status_enum) OR (confirmed_by IS NOT NULL)))
);

ALTER TABLE ONLY civix.hypothesis FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.hypothesis OWNER TO postgres;

--
-- Name: hypothesis_support; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.hypothesis_support (
    support_id uuid DEFAULT gen_random_uuid() NOT NULL,
    hypothesis_id uuid NOT NULL,
    assertion_id uuid NOT NULL,
    stance civix.support_stance_enum NOT NULL,
    weight numeric(5,4) DEFAULT 1.0 NOT NULL,
    assigned_by uuid,
    analysis_run_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.hypothesis_support FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.hypothesis_support OWNER TO postgres;

--
-- Name: identity_candidate; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_candidate (
    candidate_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_identity_id uuid NOT NULL,
    proposed_person_id uuid NOT NULL,
    ai_confidence numeric(5,4) NOT NULL,
    analysis_run_id uuid NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_ai_confidence CHECK (((ai_confidence >= (0)::numeric) AND (ai_confidence <= (1)::numeric)))
);


ALTER TABLE civix.identity_candidate OWNER TO postgres;

--
-- Name: identity_merge_event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_merge_event (
    merge_event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_identity_a uuid NOT NULL,
    source_identity_b uuid NOT NULL,
    merged_into_person_id uuid NOT NULL,
    resolution_id uuid NOT NULL,
    decided_by uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    reason text
);


ALTER TABLE civix.identity_merge_event OWNER TO postgres;

--
-- Name: identity_resolution; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_resolution (
    resolution_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_identity_id uuid NOT NULL,
    candidate_id uuid,
    resolved_person_id uuid,
    status civix.identity_resolution_status_enum NOT NULL,
    decided_by uuid,
    decision_notes text,
    superseded_by uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    CONSTRAINT chk_identity_resolution_status CHECK (((status <> 'ACCEPTED'::civix.identity_resolution_status_enum) OR (resolved_person_id IS NOT NULL)))
);


ALTER TABLE civix.identity_resolution OWNER TO postgres;

--
-- Name: identity_split_event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_split_event (
    split_event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    original_resolution_id uuid NOT NULL,
    split_source_identity_a uuid NOT NULL,
    split_source_identity_b uuid NOT NULL,
    new_person_b_id uuid NOT NULL,
    decided_by uuid NOT NULL,
    reason text NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.identity_split_event OWNER TO postgres;

--
-- Name: investigation_task; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.investigation_task (
    task_id uuid DEFAULT gen_random_uuid() NOT NULL,
    lead_id uuid,
    case_id uuid NOT NULL,
    task_type civix.task_type_enum NOT NULL,
    assigned_to uuid,
    status civix.task_status_enum DEFAULT 'PENDING'::civix.task_status_enum NOT NULL,
    due_date date,
    outcome_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.investigation_task FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.investigation_task OWNER TO postgres;

--
-- Name: investigative_case; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.investigative_case (
    case_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_number text NOT NULL,
    title text NOT NULL,
    case_type civix.case_type_enum NOT NULL,
    status civix.case_status_enum DEFAULT 'OPEN'::civix.case_status_enum NOT NULL,
    priority civix.case_priority_enum DEFAULT 'MEDIUM'::civix.case_priority_enum NOT NULL,
    jurisdiction text NOT NULL,
    investigating_unit text,
    opened_at date NOT NULL,
    closed_at date,
    lead_investigator_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT chk_case_closed_date CHECK (((closed_at IS NULL) OR (closed_at >= opened_at)))
);

ALTER TABLE ONLY civix.investigative_case FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.investigative_case OWNER TO postgres;

--
-- Name: investigative_lead; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.investigative_lead (
    lead_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    generated_by_run_id uuid,
    generated_by_person uuid,
    lead_text text NOT NULL,
    explanation text,
    priority civix.lead_priority_enum DEFAULT 'MEDIUM'::civix.lead_priority_enum NOT NULL,
    status civix.lead_status_enum DEFAULT 'OPEN'::civix.lead_status_enum NOT NULL,
    ai_confidence numeric(5,4),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    disposition_notes text,
    disposed_by uuid,
    disposed_at timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_lead_generator CHECK (((generated_by_run_id IS NOT NULL) OR (generated_by_person IS NOT NULL)))
);

ALTER TABLE ONLY civix.investigative_lead FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.investigative_lead OWNER TO postgres;

--
-- Name: legal_restriction; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.legal_restriction (
    restriction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    target_entity_id uuid,
    target_artifact_id uuid,
    restriction_type civix.legal_restriction_type_enum NOT NULL,
    authority text NOT NULL,
    court_order_reference text,
    effective_range tstzrange NOT NULL,
    scope text NOT NULL,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    created_by uuid NOT NULL,
    lifted_by uuid,
    lifted_at timestamp with time zone,
    CONSTRAINT chk_restriction_target CHECK (((target_entity_id IS NOT NULL) OR (target_artifact_id IS NOT NULL)))
);


ALTER TABLE civix.legal_restriction OWNER TO postgres;

--
-- Name: location; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.location (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'LOCATION'::civix.entity_type_enum NOT NULL,
    location_name text,
    location_type civix.location_type_enum NOT NULL,
    uncertainty_radius_meters double precision,
    altitude_meters double precision,
    azimuth_degrees double precision,
    beamwidth_degrees double precision,
    source_record_id uuid,
    generation_run_id uuid,
    geometry public.geometry(Geometry,4326) NOT NULL,
    CONSTRAINT chk_entity_type_location CHECK ((entity_type = 'LOCATION'::civix.entity_type_enum))
);


ALTER TABLE civix.location OWNER TO postgres;

--
-- Name: medical_report; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.medical_report (
    report_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    examination_type text NOT NULL,
    findings_summary text,
    practitioner_name text,
    examination_date date,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.medical_report FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.medical_report OWNER TO postgres;

--
-- Name: network; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.network (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'NETWORK'::civix.entity_type_enum NOT NULL,
    network_name text NOT NULL,
    network_type text NOT NULL,
    notes text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_network CHECK ((entity_type = 'NETWORK'::civix.entity_type_enum))
);


ALTER TABLE civix.network OWNER TO postgres;

--
-- Name: observation; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.observation (
    observation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    observer_type text NOT NULL,
    observed_by uuid,
    observation_type text,
    observation_text text,
    structured_content jsonb,
    observed_at timestamp with time zone NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.observation FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.observation OWNER TO postgres;

--
-- Name: organization; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.organization (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'ORGANIZATION'::civix.entity_type_enum NOT NULL,
    legal_name text NOT NULL,
    org_type text NOT NULL,
    registration_number text,
    incorporation_date date,
    jurisdiction text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_organization CHECK ((entity_type = 'ORGANIZATION'::civix.entity_type_enum))
);


ALTER TABLE civix.organization OWNER TO postgres;

--
-- Name: outbox; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.outbox (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    action text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    consumed_at timestamp with time zone
);


ALTER TABLE civix.outbox OWNER TO postgres;

--
-- Name: person; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.person (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'PERSON'::civix.entity_type_enum NOT NULL,
    display_name text NOT NULL,
    date_of_birth date,
    gender text,
    nationality character varying(3),
    is_deceased boolean DEFAULT false NOT NULL,
    deceased_at date,
    notes text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_person CHECK ((entity_type = 'PERSON'::civix.entity_type_enum))
);


ALTER TABLE civix.person OWNER TO postgres;

--
-- Name: person_alias; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.person_alias (
    alias_id uuid DEFAULT gen_random_uuid() NOT NULL,
    person_id uuid NOT NULL,
    alias_value text NOT NULL,
    alias_type text NOT NULL,
    source_record_id uuid,
    valid_from date,
    valid_to date,
    tx_start timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.person_alias OWNER TO postgres;

--
-- Name: phone_number; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.phone_number (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'PHONE_NUMBER'::civix.entity_type_enum NOT NULL,
    msisdn character varying(15) NOT NULL,
    country_code character varying(3) DEFAULT 'IND'::character varying,
    operator text,
    number_type text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_phone_number CHECK ((entity_type = 'PHONE_NUMBER'::civix.entity_type_enum))
);


ALTER TABLE civix.phone_number OWNER TO postgres;

--
-- Name: property; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.property (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'PROPERTY'::civix.entity_type_enum NOT NULL,
    property_ref text NOT NULL,
    property_type text NOT NULL,
    area_sqm numeric,
    description text,
    generation_run_id uuid,
    boundary_geometry public.geometry(Polygon,4326),
    CONSTRAINT chk_entity_type_property CHECK ((entity_type = 'PROPERTY'::civix.entity_type_enum))
);


ALTER TABLE civix.property OWNER TO postgres;

--
-- Name: provenance; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.provenance (
    provenance_id uuid DEFAULT gen_random_uuid() NOT NULL,
    derived_type text NOT NULL,
    derived_id uuid NOT NULL,
    source_type text NOT NULL,
    source_id uuid NOT NULL,
    derivation_method text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.provenance OWNER TO postgres;

--
-- Name: scenario; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.scenario (
    scenario_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    config_metadata json
);


ALTER TABLE civix.scenario OWNER TO postgres;

--
-- Name: sim; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.sim (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'SIM'::civix.entity_type_enum NOT NULL,
    iccid character varying(22) NOT NULL,
    imsi character varying(15),
    issuing_operator text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_sim CHECK ((entity_type = 'SIM'::civix.entity_type_enum))
);


ALTER TABLE civix.sim OWNER TO postgres;

--
-- Name: sim_in_device; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.sim_in_device (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    sim_id uuid NOT NULL,
    device_id uuid NOT NULL,
    valid_time tstzrange NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.sim_in_device OWNER TO postgres;

--
-- Name: sim_number_assignment; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.sim_number_assignment (
    assignment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    sim_id uuid NOT NULL,
    phone_number_id uuid NOT NULL,
    valid_time tstzrange NOT NULL,
    source_record_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.sim_number_assignment OWNER TO postgres;

--
-- Name: source; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.source (
    source_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_name text NOT NULL,
    agency_type text NOT NULL,
    reliability_score numeric(3,2),
    jurisdiction text,
    is_identity_protected boolean DEFAULT false NOT NULL,
    source_handler_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_reliability_score CHECK (((reliability_score >= 0.0) AND (reliability_score <= 1.0)))
);


ALTER TABLE civix.source OWNER TO postgres;

--
-- Name: source_identity; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.source_identity (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'SOURCE_IDENTITY'::civix.entity_type_enum NOT NULL,
    raw_identifier text NOT NULL,
    identifier_type civix.source_identity_type_enum NOT NULL,
    source_record_id uuid,
    observed_at timestamp with time zone NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_source_identity CHECK ((entity_type = 'SOURCE_IDENTITY'::civix.entity_type_enum))
);


ALTER TABLE civix.source_identity OWNER TO postgres;

--
-- Name: source_record; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.source_record (
    source_record_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_id uuid NOT NULL,
    external_reference text,
    record_type text NOT NULL,
    raw_content_hash bytea,
    received_at timestamp with time zone DEFAULT now() NOT NULL,
    superseded_by uuid,
    generation_run_id uuid
);


ALTER TABLE civix.source_record OWNER TO postgres;

--
-- Name: vehicle; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.vehicle (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'VEHICLE'::civix.entity_type_enum NOT NULL,
    registration_number text NOT NULL,
    vin text,
    make text,
    model text,
    color text,
    vehicle_type text NOT NULL,
    registration_year integer,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_vehicle CHECK ((entity_type = 'VEHICLE'::civix.entity_type_enum))
);


ALTER TABLE civix.vehicle OWNER TO postgres;

--
-- Name: account_holder account_holder_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_pkey PRIMARY KEY (holder_id);


--
-- Name: analysis_run analysis_run_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.analysis_run
    ADD CONSTRAINT analysis_run_pkey PRIMARY KEY (run_id);


--
-- Name: assertion assertion_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_pkey PRIMARY KEY (assertion_id);


--
-- Name: audit_event audit_event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.audit_event
    ADD CONSTRAINT audit_event_pkey PRIMARY KEY (audit_id);


--
-- Name: case_access case_access_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_pkey PRIMARY KEY (access_id);


--
-- Name: case_entity_role case_entity_role_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_pkey PRIMARY KEY (role_id);


--
-- Name: case_link case_link_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_pkey PRIMARY KEY (link_id);


--
-- Name: civix_user civix_user_external_auth_id_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.civix_user
    ADD CONSTRAINT civix_user_external_auth_id_key UNIQUE (external_auth_id);


--
-- Name: civix_user civix_user_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.civix_user
    ADD CONSTRAINT civix_user_pkey PRIMARY KEY (user_id);


--
-- Name: civix_user civix_user_username_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.civix_user
    ADD CONSTRAINT civix_user_username_key UNIQUE (username);


--
-- Name: data_quality_issue data_quality_issue_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.data_quality_issue
    ADD CONSTRAINT data_quality_issue_pkey PRIMARY KEY (issue_id);


--
-- Name: dataset dataset_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.dataset
    ADD CONSTRAINT dataset_pkey PRIMARY KEY (dataset_id);


--
-- Name: device device_imei_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_imei_key UNIQUE (imei);


--
-- Name: device device_mac_address_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_mac_address_key UNIQUE (mac_address);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (entity_id);


--
-- Name: entity entity_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT entity_pkey PRIMARY KEY (entity_id);


--
-- Name: event_participant event_participant_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_pkey PRIMARY KEY (participant_id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (event_id);


--
-- Name: evidence_artifact evidence_artifact_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_artifact
    ADD CONSTRAINT evidence_artifact_pkey PRIMARY KEY (artifact_id);


--
-- Name: evidence_instance evidence_instance_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_pkey PRIMARY KEY (instance_id);


--
-- Name: sim_in_device excl_sim_in_device; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT excl_sim_in_device EXCLUDE USING gist (sim_id WITH =, valid_time WITH &&);


--
-- Name: sim_number_assignment excl_sim_number_assignment; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT excl_sim_number_assignment EXCLUDE USING gist (phone_number_id WITH =, valid_time WITH &&);


--
-- Name: extraction extraction_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_pkey PRIMARY KEY (extraction_id);


--
-- Name: financial_account financial_account_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.financial_account
    ADD CONSTRAINT financial_account_pkey PRIMARY KEY (entity_id);


--
-- Name: fir fir_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_pkey PRIMARY KEY (fir_id);


--
-- Name: forensic_report forensic_report_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.forensic_report
    ADD CONSTRAINT forensic_report_pkey PRIMARY KEY (report_id);


--
-- Name: generation_run generation_run_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.generation_run
    ADD CONSTRAINT generation_run_pkey PRIMARY KEY (generation_run_id);


--
-- Name: hypothesis hypothesis_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_pkey PRIMARY KEY (hypothesis_id);


--
-- Name: hypothesis_support hypothesis_support_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_pkey PRIMARY KEY (support_id);


--
-- Name: identity_candidate identity_candidate_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_pkey PRIMARY KEY (candidate_id);


--
-- Name: identity_merge_event identity_merge_event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_pkey PRIMARY KEY (merge_event_id);


--
-- Name: identity_resolution identity_resolution_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_pkey PRIMARY KEY (resolution_id);


--
-- Name: identity_split_event identity_split_event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_pkey PRIMARY KEY (split_event_id);


--
-- Name: investigation_task investigation_task_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_pkey PRIMARY KEY (task_id);


--
-- Name: investigative_case investigative_case_case_number_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_case_number_key UNIQUE (case_number);


--
-- Name: investigative_case investigative_case_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_pkey PRIMARY KEY (case_id);


--
-- Name: investigative_lead investigative_lead_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_pkey PRIMARY KEY (lead_id);


--
-- Name: legal_restriction legal_restriction_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_pkey PRIMARY KEY (restriction_id);


--
-- Name: location location_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_pkey PRIMARY KEY (entity_id);


--
-- Name: medical_report medical_report_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.medical_report
    ADD CONSTRAINT medical_report_pkey PRIMARY KEY (report_id);


--
-- Name: network network_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.network
    ADD CONSTRAINT network_pkey PRIMARY KEY (entity_id);


--
-- Name: observation observation_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_pkey PRIMARY KEY (observation_id);


--
-- Name: organization organization_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (entity_id);


--
-- Name: outbox outbox_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.outbox
    ADD CONSTRAINT outbox_pkey PRIMARY KEY (id);


--
-- Name: person_alias person_alias_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT person_alias_pkey PRIMARY KEY (alias_id);


--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (entity_id);


--
-- Name: phone_number phone_number_msisdn_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_msisdn_key UNIQUE (msisdn);


--
-- Name: phone_number phone_number_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_pkey PRIMARY KEY (entity_id);


--
-- Name: property property_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.property
    ADD CONSTRAINT property_pkey PRIMARY KEY (entity_id);


--
-- Name: provenance provenance_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.provenance
    ADD CONSTRAINT provenance_pkey PRIMARY KEY (provenance_id);


--
-- Name: scenario scenario_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.scenario
    ADD CONSTRAINT scenario_pkey PRIMARY KEY (scenario_id);


--
-- Name: sim sim_iccid_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_iccid_key UNIQUE (iccid);


--
-- Name: sim sim_imsi_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_imsi_key UNIQUE (imsi);


--
-- Name: sim_in_device sim_in_device_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_pkey PRIMARY KEY (id);


--
-- Name: sim_number_assignment sim_number_assignment_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_pkey PRIMARY KEY (assignment_id);


--
-- Name: sim sim_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_pkey PRIMARY KEY (entity_id);


--
-- Name: source_identity source_identity_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_pkey PRIMARY KEY (entity_id);


--
-- Name: source source_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source
    ADD CONSTRAINT source_pkey PRIMARY KEY (source_id);


--
-- Name: source_record source_record_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_pkey PRIMARY KEY (source_record_id);


--
-- Name: source source_source_name_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source
    ADD CONSTRAINT source_source_name_key UNIQUE (source_name);


--
-- Name: case_access uq_case_access; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT uq_case_access UNIQUE (case_id, user_id);


--
-- Name: case_entity_role uq_case_entity_role; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT uq_case_entity_role UNIQUE (case_id, entity_id, role);


--
-- Name: entity uq_entity_id_type; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT uq_entity_id_type UNIQUE (entity_id, entity_type);


--
-- Name: event_participant uq_event_participant; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT uq_event_participant UNIQUE (event_id, entity_id, participant_role);


--
-- Name: evidence_artifact uq_evidence_artifact_hash; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_artifact
    ADD CONSTRAINT uq_evidence_artifact_hash UNIQUE (sha256_hash, hash_algorithm);


--
-- Name: hypothesis_support uq_hypothesis_support; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT uq_hypothesis_support UNIQUE (hypothesis_id, assertion_id);


--
-- Name: identity_candidate uq_identity_candidate; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT uq_identity_candidate UNIQUE (source_identity_id, proposed_person_id);


--
-- Name: person_alias uq_person_alias; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT uq_person_alias UNIQUE (person_id, alias_value, alias_type);


--
-- Name: vehicle vehicle_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_pkey PRIMARY KEY (entity_id);


--
-- Name: vehicle vehicle_registration_number_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_registration_number_key UNIQUE (registration_number);


--
-- Name: vehicle vehicle_vin_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_vin_key UNIQUE (vin);


--
-- Name: audit_event block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.audit_event FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: evidence_artifact block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.evidence_artifact FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: identity_merge_event block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.identity_merge_event FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: identity_resolution block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.identity_resolution FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: identity_split_event block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.identity_split_event FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: legal_restriction block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.legal_restriction FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: provenance block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.provenance FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: source_record block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.source_record FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: account_holder enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.account_holder FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: assertion enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.assertion FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: case_entity_role enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.case_entity_role FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: case_link enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.case_link FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: device enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.device FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: event enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.event FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: event_participant enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.event_participant FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: extraction enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.extraction FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: financial_account enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.financial_account FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: fir enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.fir FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: forensic_report enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.forensic_report FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: hypothesis enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.hypothesis FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: hypothesis_support enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.hypothesis_support FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: investigation_task enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.investigation_task FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: investigative_lead enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.investigative_lead FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: location enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.location FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: medical_report enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.medical_report FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: network enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.network FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: observation enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.observation FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: organization enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.organization FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: person enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.person FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: phone_number enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.phone_number FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: property enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.property FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: sim enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.sim FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: sim_in_device enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.sim_in_device FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: sim_number_assignment enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.sim_number_assignment FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: vehicle enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.vehicle FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: account_holder account_holder_account_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_account_id_fkey FOREIGN KEY (account_id) REFERENCES civix.financial_account(entity_id);


--
-- Name: account_holder account_holder_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: account_holder account_holder_holder_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_holder_entity_id_fkey FOREIGN KEY (holder_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: account_holder account_holder_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: analysis_run analysis_run_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.analysis_run
    ADD CONSTRAINT analysis_run_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: analysis_run analysis_run_initiated_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.analysis_run
    ADD CONSTRAINT analysis_run_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES civix.civix_user(user_id);


--
-- Name: assertion assertion_asserted_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_asserted_by_fkey FOREIGN KEY (asserted_by) REFERENCES civix.civix_user(user_id);


--
-- Name: assertion assertion_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: assertion assertion_object_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_object_entity_id_fkey FOREIGN KEY (object_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: assertion assertion_object_location_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_object_location_id_fkey FOREIGN KEY (object_location_id) REFERENCES civix.location(entity_id);


--
-- Name: assertion assertion_source_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_source_analysis_run_id_fkey FOREIGN KEY (source_analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: assertion assertion_subject_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_subject_entity_id_fkey FOREIGN KEY (subject_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: audit_event audit_event_case_context_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.audit_event
    ADD CONSTRAINT audit_event_case_context_id_fkey FOREIGN KEY (case_context_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: audit_event audit_event_user_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.audit_event
    ADD CONSTRAINT audit_event_user_id_fkey FOREIGN KEY (user_id) REFERENCES civix.civix_user(user_id);


--
-- Name: case_access case_access_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: case_access case_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_access case_access_revoked_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_revoked_by_fkey FOREIGN KEY (revoked_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_access case_access_user_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES civix.civix_user(user_id);


--
-- Name: case_entity_role case_entity_role_assigned_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_entity_role case_entity_role_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: case_entity_role case_entity_role_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: case_entity_role case_entity_role_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: case_link case_link_authorized_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_authorized_by_fkey FOREIGN KEY (authorized_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_link case_link_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: case_link case_link_source_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_source_case_id_fkey FOREIGN KEY (source_case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: case_link case_link_target_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_target_case_id_fkey FOREIGN KEY (target_case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: data_quality_issue data_quality_issue_detection_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.data_quality_issue
    ADD CONSTRAINT data_quality_issue_detection_run_id_fkey FOREIGN KEY (detection_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: data_quality_issue data_quality_issue_resolved_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.data_quality_issue
    ADD CONSTRAINT data_quality_issue_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES civix.civix_user(user_id);


--
-- Name: device device_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: device device_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: entity entity_created_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT entity_created_by_fkey FOREIGN KEY (created_by) REFERENCES civix.civix_user(user_id);


--
-- Name: entity entity_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT entity_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: event event_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event
    ADD CONSTRAINT event_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: event_participant event_participant_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: event_participant event_participant_event_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_event_id_fkey FOREIGN KEY (event_id) REFERENCES civix.event(event_id);


--
-- Name: event_participant event_participant_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: event event_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event
    ADD CONSTRAINT event_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: evidence_instance evidence_instance_acquired_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_acquired_by_fkey FOREIGN KEY (acquired_by) REFERENCES civix.civix_user(user_id);


--
-- Name: evidence_instance evidence_instance_artifact_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_artifact_id_fkey FOREIGN KEY (artifact_id) REFERENCES civix.evidence_artifact(artifact_id);


--
-- Name: evidence_instance evidence_instance_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: evidence_instance evidence_instance_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: evidence_instance evidence_instance_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: extraction extraction_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: extraction extraction_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: extraction extraction_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: extraction extraction_superseded_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES civix.extraction(extraction_id);


--
-- Name: financial_account financial_account_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.financial_account
    ADD CONSTRAINT financial_account_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: financial_account financial_account_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.financial_account
    ADD CONSTRAINT financial_account_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: fir fir_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: fir fir_complainant_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_complainant_entity_id_fkey FOREIGN KEY (complainant_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: fir fir_filed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_filed_by_fkey FOREIGN KEY (filed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: fir fir_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: fir fir_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: forensic_report forensic_report_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.forensic_report
    ADD CONSTRAINT forensic_report_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: forensic_report forensic_report_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.forensic_report
    ADD CONSTRAINT forensic_report_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: generation_run generation_run_dataset_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.generation_run
    ADD CONSTRAINT generation_run_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES civix.dataset(dataset_id);


--
-- Name: generation_run generation_run_scenario_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.generation_run
    ADD CONSTRAINT generation_run_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES civix.scenario(scenario_id);


--
-- Name: hypothesis hypothesis_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: hypothesis hypothesis_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: hypothesis hypothesis_created_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_created_by_fkey FOREIGN KEY (created_by) REFERENCES civix.civix_user(user_id);


--
-- Name: hypothesis hypothesis_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: hypothesis_support hypothesis_support_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: hypothesis_support hypothesis_support_assertion_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_assertion_id_fkey FOREIGN KEY (assertion_id) REFERENCES civix.assertion(assertion_id);


--
-- Name: hypothesis_support hypothesis_support_assigned_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES civix.civix_user(user_id);


--
-- Name: hypothesis_support hypothesis_support_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: hypothesis_support hypothesis_support_hypothesis_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_hypothesis_id_fkey FOREIGN KEY (hypothesis_id) REFERENCES civix.hypothesis(hypothesis_id);


--
-- Name: identity_candidate identity_candidate_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: identity_candidate identity_candidate_proposed_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_proposed_person_id_fkey FOREIGN KEY (proposed_person_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_candidate identity_candidate_source_identity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_source_identity_id_fkey FOREIGN KEY (source_identity_id) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_merge_event identity_merge_event_decided_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES civix.civix_user(user_id);


--
-- Name: identity_merge_event identity_merge_event_merged_into_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_merged_into_person_id_fkey FOREIGN KEY (merged_into_person_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_merge_event identity_merge_event_resolution_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_resolution_id_fkey FOREIGN KEY (resolution_id) REFERENCES civix.identity_resolution(resolution_id);


--
-- Name: identity_merge_event identity_merge_event_source_identity_a_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_source_identity_a_fkey FOREIGN KEY (source_identity_a) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_merge_event identity_merge_event_source_identity_b_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_source_identity_b_fkey FOREIGN KEY (source_identity_b) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_resolution identity_resolution_candidate_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES civix.identity_candidate(candidate_id);


--
-- Name: identity_resolution identity_resolution_decided_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES civix.civix_user(user_id);


--
-- Name: identity_resolution identity_resolution_resolved_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_resolved_person_id_fkey FOREIGN KEY (resolved_person_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_resolution identity_resolution_source_identity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_source_identity_id_fkey FOREIGN KEY (source_identity_id) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_resolution identity_resolution_superseded_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES civix.identity_resolution(resolution_id);


--
-- Name: identity_split_event identity_split_event_decided_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES civix.civix_user(user_id);


--
-- Name: identity_split_event identity_split_event_new_person_b_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_new_person_b_id_fkey FOREIGN KEY (new_person_b_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_split_event identity_split_event_original_resolution_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_original_resolution_id_fkey FOREIGN KEY (original_resolution_id) REFERENCES civix.identity_resolution(resolution_id);


--
-- Name: identity_split_event identity_split_event_split_source_identity_a_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_split_source_identity_a_fkey FOREIGN KEY (split_source_identity_a) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_split_event identity_split_event_split_source_identity_b_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_split_source_identity_b_fkey FOREIGN KEY (split_source_identity_b) REFERENCES civix.source_identity(entity_id);


--
-- Name: investigation_task investigation_task_assigned_to_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES civix.civix_user(user_id);


--
-- Name: investigation_task investigation_task_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: investigation_task investigation_task_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: investigation_task investigation_task_lead_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES civix.investigative_lead(lead_id);


--
-- Name: investigative_case investigative_case_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: investigative_case investigative_case_lead_investigator_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_lead_investigator_id_fkey FOREIGN KEY (lead_investigator_id) REFERENCES civix.civix_user(user_id);


--
-- Name: investigative_lead investigative_lead_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: investigative_lead investigative_lead_disposed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_disposed_by_fkey FOREIGN KEY (disposed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: investigative_lead investigative_lead_generated_by_person_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_generated_by_person_fkey FOREIGN KEY (generated_by_person) REFERENCES civix.civix_user(user_id);


--
-- Name: investigative_lead investigative_lead_generated_by_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_generated_by_run_id_fkey FOREIGN KEY (generated_by_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: investigative_lead investigative_lead_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: legal_restriction legal_restriction_created_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_created_by_fkey FOREIGN KEY (created_by) REFERENCES civix.civix_user(user_id);


--
-- Name: legal_restriction legal_restriction_lifted_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_lifted_by_fkey FOREIGN KEY (lifted_by) REFERENCES civix.civix_user(user_id);


--
-- Name: legal_restriction legal_restriction_target_artifact_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_target_artifact_id_fkey FOREIGN KEY (target_artifact_id) REFERENCES civix.evidence_artifact(artifact_id);


--
-- Name: legal_restriction legal_restriction_target_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_target_entity_id_fkey FOREIGN KEY (target_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: location location_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: location location_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: location location_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: medical_report medical_report_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.medical_report
    ADD CONSTRAINT medical_report_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: medical_report medical_report_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.medical_report
    ADD CONSTRAINT medical_report_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: network network_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.network
    ADD CONSTRAINT network_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: network network_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.network
    ADD CONSTRAINT network_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: observation observation_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: observation observation_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: observation observation_observed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_observed_by_fkey FOREIGN KEY (observed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: organization organization_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.organization
    ADD CONSTRAINT organization_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: organization organization_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.organization
    ADD CONSTRAINT organization_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: person_alias person_alias_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT person_alias_person_id_fkey FOREIGN KEY (person_id) REFERENCES civix.person(entity_id);


--
-- Name: person_alias person_alias_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT person_alias_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: person person_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person
    ADD CONSTRAINT person_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: person person_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person
    ADD CONSTRAINT person_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: phone_number phone_number_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: phone_number phone_number_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: property property_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.property
    ADD CONSTRAINT property_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: property property_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.property
    ADD CONSTRAINT property_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim sim_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: sim sim_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim_in_device sim_in_device_device_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_device_id_fkey FOREIGN KEY (device_id) REFERENCES civix.device(entity_id);


--
-- Name: sim_in_device sim_in_device_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim_in_device sim_in_device_sim_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_sim_id_fkey FOREIGN KEY (sim_id) REFERENCES civix.sim(entity_id);


--
-- Name: sim_number_assignment sim_number_assignment_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim_number_assignment sim_number_assignment_phone_number_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_phone_number_id_fkey FOREIGN KEY (phone_number_id) REFERENCES civix.phone_number(entity_id);


--
-- Name: sim_number_assignment sim_number_assignment_sim_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_sim_id_fkey FOREIGN KEY (sim_id) REFERENCES civix.sim(entity_id);


--
-- Name: sim_number_assignment sim_number_assignment_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: source_identity source_identity_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: source_identity source_identity_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: source_identity source_identity_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: source_record source_record_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: source_record source_record_source_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_source_id_fkey FOREIGN KEY (source_id) REFERENCES civix.source(source_id);


--
-- Name: source_record source_record_superseded_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES civix.source_record(source_record_id);


--
-- Name: source source_source_handler_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source
    ADD CONSTRAINT source_source_handler_id_fkey FOREIGN KEY (source_handler_id) REFERENCES civix.civix_user(user_id);


--
-- Name: vehicle vehicle_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: vehicle vehicle_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: case_entity_role; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.case_entity_role ENABLE ROW LEVEL SECURITY;

--
-- Name: case_entity_role case_entity_role_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY case_entity_role_access_policy ON civix.case_entity_role USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_entity_role.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_entity_role.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: case_link; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.case_link ENABLE ROW LEVEL SECURITY;

--
-- Name: case_link case_link_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY case_link_access_policy ON civix.case_link USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_link.source_case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_link.source_case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: evidence_instance; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.evidence_instance ENABLE ROW LEVEL SECURITY;

--
-- Name: evidence_instance evidence_instance_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY evidence_instance_access_policy ON civix.evidence_instance USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = evidence_instance.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = evidence_instance.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: extraction; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.extraction ENABLE ROW LEVEL SECURITY;

--
-- Name: extraction extraction_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY extraction_access_policy ON civix.extraction USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = extraction.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = extraction.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: fir; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.fir ENABLE ROW LEVEL SECURITY;

--
-- Name: fir fir_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY fir_access_policy ON civix.fir USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = fir.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = fir.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: forensic_report; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.forensic_report ENABLE ROW LEVEL SECURITY;

--
-- Name: forensic_report forensic_report_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY forensic_report_access_policy ON civix.forensic_report USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = forensic_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = forensic_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: hypothesis; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.hypothesis ENABLE ROW LEVEL SECURITY;

--
-- Name: hypothesis hypothesis_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY hypothesis_access_policy ON civix.hypothesis USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = hypothesis.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = hypothesis.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: hypothesis_support; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.hypothesis_support ENABLE ROW LEVEL SECURITY;

--
-- Name: hypothesis_support hypothesis_support_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY hypothesis_support_access_policy ON civix.hypothesis_support USING ((EXISTS ( SELECT 1
   FROM (civix.hypothesis h
     JOIN civix.case_access ca ON ((h.case_id = ca.case_id)))
  WHERE ((h.hypothesis_id = hypothesis_support.hypothesis_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.hypothesis h
     JOIN civix.case_access ca ON ((h.case_id = ca.case_id)))
  WHERE ((h.hypothesis_id = hypothesis_support.hypothesis_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: investigation_task; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.investigation_task ENABLE ROW LEVEL SECURITY;

--
-- Name: investigation_task investigation_task_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY investigation_task_access_policy ON civix.investigation_task USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigation_task.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigation_task.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: investigative_case; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.investigative_case ENABLE ROW LEVEL SECURITY;

--
-- Name: investigative_case investigative_case_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY investigative_case_access_policy ON civix.investigative_case USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_case.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_case.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: investigative_lead; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.investigative_lead ENABLE ROW LEVEL SECURITY;

--
-- Name: investigative_lead investigative_lead_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY investigative_lead_access_policy ON civix.investigative_lead USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_lead.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_lead.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: medical_report; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.medical_report ENABLE ROW LEVEL SECURITY;

--
-- Name: medical_report medical_report_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY medical_report_access_policy ON civix.medical_report USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = medical_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = medical_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: observation; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.observation ENABLE ROW LEVEL SECURITY;

--
-- Name: observation observation_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY observation_access_policy ON civix.observation USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = observation.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = observation.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: SCHEMA civix; Type: ACL; Schema: -; Owner: postgres
--

GRANT USAGE ON SCHEMA civix TO civix_api;


--
-- Name: TABLE account_holder; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.account_holder TO civix_api;


--
-- Name: TABLE analysis_run; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.analysis_run TO civix_api;


--
-- Name: TABLE assertion; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.assertion TO civix_api;


--
-- Name: TABLE audit_event; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE civix.audit_event TO civix_api;


--
-- Name: TABLE case_access; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.case_access TO civix_api;


--
-- Name: TABLE case_entity_role; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.case_entity_role TO civix_api;


--
-- Name: TABLE case_link; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.case_link TO civix_api;


--
-- Name: TABLE civix_user; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.civix_user TO civix_api;


--
-- Name: TABLE data_quality_issue; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.data_quality_issue TO civix_api;


--
-- Name: TABLE dataset; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.dataset TO civix_api;


--
-- Name: TABLE device; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.device TO civix_api;


--
-- Name: TABLE entity; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.entity TO civix_api;


--
-- Name: TABLE event; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.event TO civix_api;


--
-- Name: TABLE event_participant; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.event_participant TO civix_api;


--
-- Name: TABLE evidence_artifact; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE civix.evidence_artifact TO civix_api;


--
-- Name: TABLE evidence_instance; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.evidence_instance TO civix_api;


--
-- Name: TABLE extraction; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.extraction TO civix_api;


--
-- Name: TABLE financial_account; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.financial_account TO civix_api;


--
-- Name: TABLE fir; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.fir TO civix_api;


--
-- Name: TABLE forensic_report; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.forensic_report TO civix_api;


--
-- Name: TABLE generation_run; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.generation_run TO civix_api;


--
-- Name: TABLE hypothesis; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.hypothesis TO civix_api;


--
-- Name: TABLE hypothesis_support; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.hypothesis_support TO civix_api;


--
-- Name: TABLE identity_candidate; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.identity_candidate TO civix_api;


--
-- Name: TABLE identity_merge_event; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.identity_merge_event TO civix_api;


--
-- Name: TABLE identity_resolution; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.identity_resolution TO civix_api;


--
-- Name: TABLE identity_split_event; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.identity_split_event TO civix_api;


--
-- Name: TABLE investigation_task; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.investigation_task TO civix_api;


--
-- Name: TABLE investigative_case; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.investigative_case TO civix_api;


--
-- Name: TABLE investigative_lead; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.investigative_lead TO civix_api;


--
-- Name: TABLE legal_restriction; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.legal_restriction TO civix_api;


--
-- Name: TABLE location; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.location TO civix_api;


--
-- Name: TABLE medical_report; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.medical_report TO civix_api;


--
-- Name: TABLE network; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.network TO civix_api;


--
-- Name: TABLE observation; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.observation TO civix_api;


--
-- Name: TABLE organization; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.organization TO civix_api;


--
-- Name: TABLE outbox; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.outbox TO civix_api;


--
-- Name: TABLE person; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.person TO civix_api;


--
-- Name: TABLE person_alias; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.person_alias TO civix_api;


--
-- Name: TABLE phone_number; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.phone_number TO civix_api;


--
-- Name: TABLE property; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.property TO civix_api;


--
-- Name: TABLE provenance; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT ON TABLE civix.provenance TO civix_api;


--
-- Name: TABLE scenario; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.scenario TO civix_api;


--
-- Name: TABLE sim; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.sim TO civix_api;


--
-- Name: TABLE sim_in_device; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.sim_in_device TO civix_api;


--
-- Name: TABLE sim_number_assignment; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.sim_number_assignment TO civix_api;


--
-- Name: TABLE source; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.source TO civix_api;


--
-- Name: TABLE source_identity; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.source_identity TO civix_api;


--
-- Name: TABLE source_record; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.source_record TO civix_api;


--
-- Name: TABLE vehicle; Type: ACL; Schema: civix; Owner: postgres
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE civix.vehicle TO civix_api;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: civix; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA civix GRANT SELECT,USAGE ON SEQUENCES TO civix_api;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: civix; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA civix GRANT SELECT,INSERT,DELETE,UPDATE ON TABLES TO civix_api;


--
-- PostgreSQL database dump complete
--

\unrestrict FgQE42Hro7qKrrXldpeaKzeB53pcav9hX2jW2KdkTx6ZhKuGPxs9PhXzRWfZkFV


```
</details>

---

## 4. EXHAUSTIVE PHASE 6 SECURITY FINDINGS & IMMUTABILITY

During the Phase 6/7 transition, a critical security audit uncovered severe flaws:
- **Finding:** Initial scripts heavily relied on hardcoded fallback credentials and superuser connections for operational queries.
- **Remediation:** Strict fail-closed configuration was implemented. The API explicitly uses the `civix_api` database role which possesses:
  - `rolsuper = false`
  - `rolbypassrls = false`
- **Immutability Enforcement:** The `civix_api` role explicitly lacks `UPDATE` and `DELETE` privileges on core audit and evidence tables (`audit_event`, `evidence_artifact`, `provenance`). This guarantees cryptographic-like immutability at the lowest database tier. These specific unprivileged states were empirically tested and proven to result in `ProgrammingError: permission denied` for the API role.

---

## 5. PHASE 7 TASK 1 - FASTAPI & RLS FOUNDATION

Task 1 focused on building the FastAPI foundation with strict RLS identity binding.

**RLS Identity Architecture (Approved & Verified):**
Identity configuration relies on SQLAlchemy 2.0 Async architecture (asyncpg). The user identity MUST NOT be bound at the connection-pool checkout event. Instead, it is established specifically within the request's database transaction using:
`SELECT set_config('civix.current_user_id', :user_id, true)`

### 5.1 Exhaustive API Source Code Evidence

The exact state of the foundation code is embedded below. You must use this code as your exact reference for how dependencies, database connections, and configurations are structured.

#### `civix_api/config.py`
```python
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    civix_database_url: str = ""
    civix_jwt_secret: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

if not settings.civix_database_url:
    raise ValueError("CIVIX_DATABASE_URL environment variable is missing. Halting API startup.")

if not settings.civix_database_url.startswith("postgresql+asyncpg://"):
    raise ValueError("CIVIX_DATABASE_URL must use the postgresql+asyncpg driver.")

if not settings.civix_jwt_secret:
    raise ValueError("CIVIX_JWT_SECRET environment variable is missing. Halting API startup.")

```

#### `civix_api/database.py`
```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings

# Engine configuration with pooling. We don't set pool checkout events for RLS!
# RLS MUST be established within the transaction lifecycle inside dependencies.py.

pool_size = int(os.getenv("CIVIX_API_POOL_SIZE", "5"))
max_overflow = int(os.getenv("CIVIX_API_MAX_OVERFLOW", "10"))

engine = create_async_engine(
    settings.civix_database_url,
    pool_size=pool_size,
    max_overflow=max_overflow,
    pool_pre_ping=True,
    echo=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False
)

```

#### `civix_api/dependencies.py`
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import AsyncGenerator

from .database import AsyncSessionLocal
from .auth.principal import AuthenticatedCivixUser
from .auth.jwt import get_user_id_from_token, oauth2_scheme

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a raw, unauthenticated DB session (useful for auth checks)."""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user_from_token(
    token: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session)
) -> AuthenticatedCivixUser:
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    user_id = get_user_id_from_token(token.credentials)
    
    # Query user from DB (run as civix_api but before RLS context is established for the endpoint)
    # This is safe because civix_user is not RLS protected in a way that hides identity rows.
    result = await session.execute(
        text("SELECT user_id, username, role, clearance_level FROM civix.civix_user WHERE user_id = :uid"),
        {"uid": user_id}
    )
    user_row = result.first()
    if not user_row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return AuthenticatedCivixUser(
        user_id=user_row[0],
        username=user_row[1],
        role=user_row[2],
        clearance_level=user_row[3]
    )

async def get_rls_session(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_db_session)
) -> AsyncGenerator[AsyncSession, None]:
    """
    Acquires an async database session and securely establishes the RLS context
    for the current transaction using a parameterized query.
    
    The identity is strictly request-scoped and transaction-local.
    """
    try:
        # We explicitly establish the transaction-local user identity
        # The third parameter `true` ensures it disappears at COMMIT/ROLLBACK.
        await session.execute(
            text("SELECT set_config('civix.current_user_id', :user_id, true)"),
            {"user_id": str(user.user_id)}
        )
        
        # Yield the RLS-configured session to the router
        yield session
        
        # Commit on successful completion of the request
        await session.commit()
    except Exception:
        # Rollback on any failure
        await session.rollback()
        raise

```

#### `civix_api/main.py`
```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager

from .database import engine
from .dependencies import get_db_session
from .routers import users, cases

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Application startup logic
    yield
    # Application shutdown logic
    await engine.dispose()

app = FastAPI(
    title="Civix 2.0 API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(users.router)
app.include_router(cases.router)

@app.get("/health")
async def health_check(session: AsyncSession = Depends(get_db_session)):
    """
    Health check endpoint verifying API and DB connectivity.
    This safely uses get_db_session() instead of get_rls_session(),
    ensuring we do NOT bypass RLS or impersonate users for a simple check.
    """
    try:
        # Simple query to verify DB is alive
        result = await session.execute(text("SELECT 1"))
        alive = result.scalar() == 1
        if not alive:
            raise HTTPException(status_code=503, detail="Database connectivity verified but returned unexpected result")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connectivity failed: {str(e)}")

```

---

## 6. PHASE 7 TASK 2A — CASE CREATION DEADLOCK & MIGRATION 010

An architectural deadlock was identified blocking safe case creation:

**The Deadlock:**
- `investigative_case` has `FORCE RLS` with a `WITH CHECK` policy requiring the authenticated user to possess a matching `case_access` row.
- `case_access.case_id` possessed a `NOT DEFERRABLE` foreign key referencing `investigative_case.case_id`.

**Verified Live Schema State Post-Migration 010:**
- The FK was dropped and recreated as `DEFERRABLE INITIALLY DEFERRED`.
- `condeferrable = true`
- `condeferred = true`
- `investigative_case` RLS constraints remain entirely active.
- `civix_api` role remains fully unprivileged.

**Verified Case Creation Sequence:**
1. Generate UUIDs for `case_id` and `access_id` in API.
2. Begin Database Transaction.
3. Establish `set_config(..., true)`.
4. `INSERT INTO civix.case_access` (Succeeds via deferred FK).
5. `INSERT INTO civix.investigative_case` (Succeeds via valid RLS context).
6. `COMMIT` (Both rows flush safely).

### 6.1 Case Access Trust Boundary (CRITICAL)

> [!IMPORTANT]
> The `civix.case_access` table currently has **RLS disabled** (`relrowsecurity = false`) and **FORCE RLS disabled**. The database currently allows the application to INSERT any mapping it wishes.
>
> **Implication:** The security trust boundary for `case_access` is entirely **APPLICATION ENFORCED**. The API must rigorously ensure that `case_access.user_id` is securely derived from the authenticated JWT principal and NEVER trusted from an arbitrary JSON payload.

---

## 7. CURRENT PHASE 7 TASK 2 STATE (IMPLEMENTATION & AUTH)

Implementation of Phase 7 Task 2 was initiated and partially completed. The following exact code represents the current un-merged, in-flight state of the API routers and JWT logic.

### 7.1 `civix_api/auth/jwt.py`
```python
import jwt
from typing import Optional
from uuid import UUID
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from civix_api.config import settings

oauth2_scheme = HTTPBearer(auto_error=False)

def get_user_id_from_token(token: str) -> UUID:
    try:
        payload = jwt.decode(
            token,
            settings.civix_jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "sub"]}
        )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing 'sub' claim in JWT.",
            )
        try:
            return UUID(str(sub))
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 'sub' claim format. Must be a valid UUID.",
            )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        )
    except jwt.exceptions.MissingRequiredClaimError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing '{e.claim}' claim in JWT.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
        )

```

### 7.2 `civix_api/auth/principal.py`
```python
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class AuthenticatedCivixUser(BaseModel):
    user_id: UUID
    username: str
    role: str
    clearance_level: str


```

### 7.3 `civix_api/routers/users.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"]
)

@router.get("/me")
async def get_current_user(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    # We query the DB again within the RLS session just to return the full profile
    # The requirement: Return only the authenticated user's own record.
    # We query civix_user which is not strictly RLS'd but we filter by the authenticated user's ID.
    result = await session.execute(
        text("""
            SELECT user_id, username, display_name, role, clearance_level, external_auth_id
            FROM civix.civix_user 
            WHERE user_id = :uid
        """),
        {"uid": user.user_id}
    )
    user_row = result.first()
    if not user_row:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    return {
        "user_id": str(user_row[0]),
        "username": user_row[1],
        "display_name": user_row[2],
        "role": user_row[3],
        "clearance_level": user_row[4],
        "external_auth_id": user_row[5]
    }

```

### 7.4 `civix_api/routers/cases.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4

from civix_api.dependencies import get_current_user_from_token, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser

router = APIRouter(
    prefix="/api/v1/cases",
    tags=["cases"]
)

class CaseCreateRequest(BaseModel):
    case_number: str
    title: str
    case_type: str
    jurisdiction: str
    priority: str = "MEDIUM"
    investigating_unit: Optional[str] = None

@router.post("")
async def create_case(
    case_data: CaseCreateRequest,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    case_id = uuid4()
    access_id = uuid4()

    # 1. Insert case_access FIRST
    await session.execute(
        text("""
            INSERT INTO civix.case_access (access_id, case_id, user_id, permission_level, granted_by)
            VALUES (:aid, :cid, :uid, 'ADMIN', :uid)
        """),
        {
            "aid": access_id,
            "cid": case_id,
            "uid": user.user_id
        }
    )

    # 2. Insert investigative_case SECOND
    await session.execute(
        text("""
            INSERT INTO civix.investigative_case (
                case_id, case_number, title, case_type, priority, jurisdiction, 
                investigating_unit, opened_at, lead_investigator_id
            )
            VALUES (
                :cid, :num, :title, :type, :prio, :jur, :unit, now(), :uid
            )
        """),
        {
            "cid": case_id,
            "num": case_data.case_number,
            "title": case_data.title,
            "type": case_data.case_type,
            "prio": case_data.priority,
            "jur": case_data.jurisdiction,
            "unit": case_data.investigating_unit,
            "uid": user.user_id
        }
    )

    # Note: commit happens automatically in the dependency generator, 
    # but we can return the case details directly.
    return {
        "case_id": str(case_id),
        "case_number": case_data.case_number,
        "title": case_data.title,
        "status": "OPEN"
    }

@router.get("")
async def list_cases(
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> List[Dict[str, Any]]:
    # RLS enforces visibility automatically
    result = await session.execute(
        text("""
            SELECT case_id, case_number, title, case_type, status, priority, jurisdiction
            FROM civix.investigative_case
            ORDER BY created_at DESC
        """)
    )
    cases = []
    for row in result.fetchall():
        cases.append({
            "case_id": str(row[0]),
            "case_number": row[1],
            "title": row[2],
            "case_type": row[3],
            "status": row[4],
            "priority": row[5],
            "jurisdiction": row[6]
        })
    return cases

@router.get("/{case_id}")
async def get_case(
    case_id: UUID,
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token),
    session: AsyncSession = Depends(get_rls_session)
) -> Dict[str, Any]:
    # RLS enforces visibility automatically
    result = await session.execute(
        text("""
            SELECT case_id, case_number, title, case_type, status, priority, jurisdiction
            FROM civix.investigative_case
            WHERE case_id = :cid
        """),
        {"cid": case_id}
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
        
    return {
        "case_id": str(row[0]),
        "case_number": row[1],
        "title": row[2],
        "case_type": row[3],
        "status": row[4],
        "priority": row[5],
        "jurisdiction": row[6]
    }

```

---

## 8. EXHAUSTIVE INTEGRATION TEST EVIDENCE

The IDE agent was paused while fixing teardown logic in the test suite. The exact code of the tests is preserved below to demonstrate what is covered: pool leakage, transaction isolation, negative runtime permissions, and JWT validation. The tests were failing intermittently due to SQLAlchemy teardown/session closure issues (fixture sharing across `create_test_user` and `db_session`), but fixes were applied just prior to halting.

### 8.1 `tests/api/conftest.py`
```python
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

from civix_api.main import app
from civix_api.database import engine, AsyncSessionLocal

from sqlalchemy import text
from uuid import uuid4

# Tell pytest to use asyncio
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSessionLocal, None]:
    async with AsyncSessionLocal() as session:
        yield session

@pytest.fixture
async def create_test_user():
    created_users = []
    
    async def _create(username=None, role="INVESTIGATOR"):
        if username is None:
            username = f"user_{uuid4().hex[:8]}"
        user_id = uuid4()
        auth_id = f"auth-{user_id}"
        async with AsyncSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES (:uid, :auth, :uname, :uname, :role)
                """),
                {"uid": user_id, "auth": auth_id, "uname": username, "role": role}
            )
            await session.commit()
        created_users.append(user_id)
        return user_id
        
    yield _create
    
    # Teardown
    async with AsyncSessionLocal() as session:
        for uid in created_users:
            await session.execute(text("RESET ROLE"))
            await session.execute(text("DELETE FROM civix.case_access WHERE user_id = :uid"), {"uid": uid})
            await session.execute(text("DELETE FROM civix.civix_user WHERE user_id = :uid"), {"uid": uid})
        await session.commit()

```

### 8.2 `tests/api/test_auth.py`
```python
import pytest
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport

from civix_api.main import app
from civix_api.config import settings

def create_token(sub: str, exp_delta: int = 3600) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=exp_delta)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_auth_missing_header():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_malformed_token():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": "Bearer malformed.token.here"})
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_invalid_signature():
    token = jwt.encode({"sub": str(uuid4()), "exp": datetime.utcnow() + timedelta(hours=1)}, "wrong_secret", algorithm="HS256")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_auth_expired_token():
    token = create_token(sub=str(uuid4()), exp_delta=-3600)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_auth_missing_sub():
    payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
    token = jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "Missing 'sub' claim" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_invalid_uuid():
    token = create_token(sub="not-a-uuid")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert "valid UUID" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_user_not_found():
    # Valid UUID but not in DB
    token = create_token(sub=str(uuid4()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_auth_valid_token(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == str(user_id)
    assert data["username"] == "testuser"

```

### 8.3 `tests/api/test_cases.py`
```python
import pytest
import jwt
from uuid import uuid4
from datetime import datetime, timedelta
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from civix_api.main import app
from civix_api.config import settings

def create_token(sub: str) -> str:
    payload = {
        "sub": sub,
        "exp": datetime.utcnow() + timedelta(seconds=3600)
    }
    return jwt.encode(payload, settings.civix_jwt_secret, algorithm="HS256")

@pytest.mark.asyncio
async def test_create_case(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    case_payload = {
        "case_number": f"TEST-{uuid4().hex[:6]}",
        "title": "Test Case Title",
        "case_type": "CRIMINAL",
        "jurisdiction": "Test Jurisdiction"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/v1/cases",
            json=case_payload,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200, response.text
    data = response.json()
    assert "case_id" in data
    assert data["case_number"] == case_payload["case_number"]

    # Verify case_access created and assigned to JWT user
    case_id = data["case_id"]
    await db_session.execute(text("RESET ROLE"))
    access_res = await db_session.execute(
        text("SELECT user_id, permission_level FROM civix.case_access WHERE case_id = :cid"),
        {"cid": case_id}
    )
    access_rows = access_res.fetchall()
    assert len(access_rows) == 1
    assert str(access_rows[0][0]) == str(user_id)
    assert access_rows[0][1] == "ADMIN"
    
    # Cleanup
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_id})
    await db_session.commit()

@pytest.mark.asyncio
async def test_case_list_and_get_isolated(db_session, create_test_user):
    user_a = await create_test_user()
    user_b = await create_test_user()
    
    token_a = create_token(sub=str(user_a))
    token_b = create_token(sub=str(user_b))
    
    # User A creates a case
    case_a_num = f"CA-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_a = await ac.post("/api/v1/cases", json={
            "case_number": case_a_num, "title": "Case A", "case_type": "CRIMINAL", "jurisdiction": "Jur A"
        }, headers={"Authorization": f"Bearer {token_a}"})
        case_a_id = res_a.json()["case_id"]

    # User B creates a case
    case_b_num = f"CB-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res_b = await ac.post("/api/v1/cases", json={
            "case_number": case_b_num, "title": "Case B", "case_type": "CRIMINAL", "jurisdiction": "Jur B"
        }, headers={"Authorization": f"Bearer {token_b}"})
        case_b_id = res_b.json()["case_id"]

    # List for User A
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        list_a = await ac.get("/api/v1/cases", headers={"Authorization": f"Bearer {token_a}"})
        cases_a = list_a.json()
        assert len([c for c in cases_a if c["case_id"] == case_a_id]) == 1
        assert len([c for c in cases_a if c["case_id"] == case_b_id]) == 0
        
        # Get case A for User A
        get_a_valid = await ac.get(f"/api/v1/cases/{case_a_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert get_a_valid.status_code == 200

        # Get case B for User A -> 404 Not Found (RLS isolated)
        get_a_invalid = await ac.get(f"/api/v1/cases/{case_b_id}", headers={"Authorization": f"Bearer {token_a}"})
        assert get_a_invalid.status_code == 404
        
    # Cleanup
    await db_session.execute(text("RESET ROLE"))
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id IN (:ca, :cb)"), {"ca": case_a_id, "cb": case_b_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id IN (:ca, :cb)"), {"ca": case_a_id, "cb": case_b_id})
    await db_session.commit()

@pytest.mark.asyncio
async def test_case_creation_failure_rollback(db_session, create_test_user):
    user_id = await create_test_user()
    token = create_token(sub=str(user_id))
    
    # We will trigger a database error on investigative_case insertion by causing a CHECK constraint or NOT NULL violation.
    # The title is technically NOT NULL in DB, but the API requires it. Let's send a bad case_type instead which will fail enum cast, or duplicate case_number.
    
    # Let's create one successfully
    case_num = f"DUP-{uuid4().hex[:6]}"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.post("/api/v1/cases", json={
            "case_number": case_num, "title": "Valid Case", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        assert res1.status_code == 200
        case_1_id = res1.json()["case_id"]
        
        # Attempt to create another with the exact same case_number (which has a UNIQUE constraint)
        # This will fail on the `investigative_case` insert.
        res2 = await ac.post("/api/v1/cases", json={
            "case_number": case_num, "title": "Dup Case", "case_type": "CRIMINAL", "jurisdiction": "Jur"
        }, headers={"Authorization": f"Bearer {token}"})
        assert res2.status_code == 500  # Unhandled sqlalchemy IntegrityError is a 500, which rolls back

    # Verify no orphaned case_access rows were created for the failed request
    await db_session.execute(text("RESET ROLE"))
    access_res = await db_session.execute(
        text("SELECT case_id FROM civix.case_access WHERE user_id = :uid"),
        {"uid": user_id}
    )
    rows = access_res.fetchall()
    # Should only have 1 (the valid case)
    assert len(rows) == 1
    assert str(rows[0][0]) == case_1_id

    # Cleanup
    await db_session.execute(text("DELETE FROM civix.case_access WHERE case_id = :cid"), {"cid": case_1_id})
    await db_session.execute(text("DELETE FROM civix.investigative_case WHERE case_id = :cid"), {"cid": case_1_id})
    await db_session.commit()

```

### 8.4 `tests/api/test_rls.py`
```python
import pytest
import uuid
import os
import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import FastAPI, Depends, HTTPException
from httpx import AsyncClient, ASGITransport

from civix_api.main import app
from civix_api.config import settings
from civix_api.dependencies import get_db_session, get_rls_session
from civix_api.auth.principal import AuthenticatedCivixUser
from civix_api.dependencies import get_current_user_from_token
# Add a test endpoint
@app.get("/test/rls")
async def verify_rls_endpoint(
    session: AsyncSession = Depends(get_rls_session),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token)
):
    # Retrieve the current RLS context from Postgres
    result = await session.execute(text("SELECT current_setting('civix.current_user_id', true)"))
    current_setting = result.scalar()
    
    # Try to select from a table using RLS to prove access
    # We will use case_entity_role as it has FORCE ROW LEVEL SECURITY.
    await session.execute(text("SELECT count(*) FROM civix.case_entity_role"))
    
    return {"current_user_id": current_setting, "requested_user_id": str(user.user_id)}

@app.get("/test/rls/error")
async def verify_rls_error_endpoint(
    session: AsyncSession = Depends(get_rls_session),
    user: AuthenticatedCivixUser = Depends(get_current_user_from_token)
):
    # Retrieve the current RLS context from Postgres
    result = await session.execute(text("SELECT current_setting('civix.current_user_id', true)"))
    current_setting = result.scalar()
    
    # Intentionally raise an exception to trigger a rollback in the dependency
    raise HTTPException(status_code=500, detail=f"Intentional Error for user {current_setting}")

@pytest.mark.asyncio
async def test_pool_leakage():
    # Force a small pool for testing leakage. Create inside the test so it binds to the current loop.
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    async def override_get_db_session():
        async with TestSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db_session] = override_get_db_session

    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    try:
        # Setup: Insert test users
        async with TestSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES 
                (:id_a, 'test_a', 'test_a', 'Test A', 'INVESTIGATOR'),
                (:id_b, 'test_b', 'test_b', 'Test B', 'INVESTIGATOR')
                """),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
            
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # We override the auth dependency to return User A
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_a_id, username="test_a", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User A
            response_a = await client.get("/test/rls")
            assert response_a.status_code == 200
            data_a = response_a.json()
            assert data_a["current_user_id"] == str(user_a_id)
            
            # Now override auth to return User B
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_b_id, username="test_b", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User B
            response_b = await client.get("/test/rls")
            assert response_b.status_code == 200
            data_b = response_b.json()
            assert data_b["current_user_id"] == str(user_b_id)
            
            # Ensure B did not inherit A's identity from the pool
            assert data_b["current_user_id"] != str(user_a_id)

    finally:
        # Cleanup overrides
        app.dependency_overrides.clear()
        
        # Cleanup DB
        async with TestSessionLocal() as session:
            await session.execute(
                text("DELETE FROM civix.civix_user WHERE user_id IN (:id_a, :id_b)"),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
            
        await test_engine.dispose()

@pytest.mark.asyncio
async def test_pool_leakage_on_rollback():
    """
    Tests that if a request crashes and rolls back, the RLS context is correctly cleared
    and does not leak to the next pooled connection.
    """
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    async def override_get_db_session():
        async with TestSessionLocal() as session:
            yield session
            
    app.dependency_overrides[get_db_session] = override_get_db_session

    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    try:
        # Setup: Insert test users
        async with TestSessionLocal() as session:
            await session.execute(
                text("""
                INSERT INTO civix.civix_user (user_id, external_auth_id, username, display_name, role)
                VALUES 
                (:id_a, 'test_a', 'test_a', 'Test A', 'INVESTIGATOR'),
                (:id_b, 'test_b', 'test_b', 'Test B', 'INVESTIGATOR')
                """),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
            
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Override auth to return User A
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_a_id, username="test_a", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User A hits the error endpoint
            response_a = await client.get("/test/rls/error")
            assert response_a.status_code == 500
            
            # Now override auth to return User B
            app.dependency_overrides[get_current_user_from_token] = lambda: AuthenticatedCivixUser(
                user_id=user_b_id, username="test_b", role="INVESTIGATOR", clearance_level="UNCLASSIFIED"
            )
            
            # Request as User B on normal endpoint
            response_b = await client.get("/test/rls")
            assert response_b.status_code == 200
            data_b = response_b.json()
            assert data_b["current_user_id"] == str(user_b_id)
            
            # Ensure B did not inherit A's identity from the pool
            assert data_b["current_user_id"] != str(user_a_id)

    finally:
        # Cleanup overrides
        app.dependency_overrides.clear()
        
        # Cleanup DB
        async with TestSessionLocal() as session:
            await session.execute(
                text("DELETE FROM civix.civix_user WHERE user_id IN (:id_a, :id_b)"),
                {"id_a": user_a_id, "id_b": user_b_id}
            )
            await session.commit()
        
        await test_engine.dispose()

@pytest.mark.asyncio
async def test_runtime_negative_permissions():
    """
    Proves that the civix_api role is actively denied UPDATE/DELETE at runtime,
    independent of any application-level logic.
    """
    test_engine = create_async_engine(
        settings.civix_database_url,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True
    )
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False, autoflush=False)
    
    from sqlalchemy.exc import ProgrammingError

    async with TestSessionLocal() as session:
        await session.execute(text("SET ROLE civix_api"))
        
        # 1. audit_event UPDATE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("UPDATE civix.audit_event SET metadata = '{}' WHERE audit_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 2. audit_event DELETE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("DELETE FROM civix.audit_event WHERE audit_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 3. evidence_artifact UPDATE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("UPDATE civix.evidence_artifact SET original_filename = 'tampered' WHERE artifact_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 4. evidence_artifact DELETE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("DELETE FROM civix.evidence_artifact WHERE artifact_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()
        
        # 5. provenance UPDATE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("UPDATE civix.provenance SET derivation_method = 'tampered' WHERE provenance_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

        # 6. provenance DELETE
        with pytest.raises(ProgrammingError) as exc_info:
            await session.execute(text("DELETE FROM civix.provenance WHERE provenance_id = '00000000-0000-0000-0000-000000000000'"))
        assert "permission denied" in str(exc_info.value)
        await session.rollback()

    await test_engine.dispose()

```

---

## 9. KNOWN RISKS / OPEN ITEMS

| ID | Issue | Severity | Current State | Required Action |
|---|---|---|---|---|
| 1 | `chain_of_custody_event` missing | High | Resolved | Utilize `evidence_artifact` and `provenance` tables going forward. |
| 2 | `case_access` Trust Boundary | Critical | Documented | API explicitly derives identity from JWT. Any future admin/sharing endpoints must actively validate the requester's permission. |
| 3 | Incomplete Test Suite Run | Medium | Resolved | (Historical risk) Test teardown fixed and suite passes 18/18. |
| 4 | Phase 7 Task 2 Completion | High | Resolved | (Historical risk) Task 2 was subsequently completed and Task 3 independently accepted. |

---

## 10. EXACT RESUME POINT (SUPERSEDED)

> [!NOTE]
> The following instructions are HISTORICAL. The repository subsequently verified the completion of Phase 7 Task 2 (18/18 tests passing) and Phase 7 Task 3 (ML Parity, independently accepted). Do not execute these stale instructions.

You must start completely fresh from this exact state. 
Do NOT redesign the architecture. Do NOT modify the PostgreSQL 16 schema. Do NOT touch migrations 001-010. 

**Next Immediate Actions (HISTORICAL):**
1. Run `pytest tests/api -v` to observe the current testing state.
2. Fix any remaining teardown or isolation bugs in `conftest.py`, `test_cases.py`, or `test_auth.py`.
3. Complete Phase 7 Task 2 by delivering a fully green test suite proving authentication, RLS case isolation, transaction rollbacks, and JWT security behavior.

## 11. FINAL VERIFICATION CHECKLIST

- [x] Repository inspected 
- [x] Live PostgreSQL 16 inspected 
- [x] PostgreSQL 17 isolation verified (Confirmed no interactions)
- [x] Alembic state verified (001-009 unmodified, 010 exists)
- [x] Migration 010 verified (`condeferrable=t` established)
- [x] RLS policy verified (`investigative_case` is `forcerowsecurity=t`)
- [x] civix_api role verified (`rolsuper=f`, `rolbypassrls=f`)
- [x] Task 1 tests verified (Authored and present, teardown fixed)
- [x] Task 2A tests verified (Authored and present)
- [x] Current Task 2 implementation inspected (Routers & JWT modules created)
- [x] Current Task 2 tests inspected (Failures observed and documented)
- [x] Exact resume point established (See Section 10)
