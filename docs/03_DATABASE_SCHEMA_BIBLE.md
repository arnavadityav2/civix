# 03 — DATABASE SCHEMA BIBLE
## Every Table, Column, FK, Constraint, and Invariant

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
