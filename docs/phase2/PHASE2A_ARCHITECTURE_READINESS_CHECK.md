# PHASE 2A — ARCHITECTURE READINESS CHECK
**Date**: 2026-08-29 | **Auditor**: Phase 2A Implementation Agent

---

## A. Documents Inspected

1. `docs/00_CIVIX_MASTER_CONTEXT.md`
2. `docs/03_DATABASE_SCHEMA_BIBLE.md` (607 lines — AUTHORITATIVE)
3. `docs/05_EPISTEMIC_MODEL.md`
4. `docs/CIVIX_CHANGE_CONTROL.md` (ADR-001 through ADR-022)
5. `docs/21_KNOWN_GAPS_AND_RISKS.md` (INV-01 through INV-20)
6. `docs/phase1_audit/GATE3_DDL_READINESS_REPORT.md` — All gates PASSED
7. `docs/phase1_audit/GATE3_BITEMPORAL_ENFORCEMENT_STANDARD.md`
8. `docs/phase1_audit/GATE3_AUTHORIZATION_BOUNDARY_STANDARD.md`
9. `docs/phase1_audit/GATE3_EVIDENCE_LIFECYCLE_STANDARD.md`
10. `docs/phase1_audit/GATE3_NEO4J_PROJECTION_STANDARD.md`
11. `docs/phase1_audit/GATE3_POLYMORPHIC_REFERENCE_STANDARD.md`
12. `database/schema_postgres.sql` — CONFIRMED SUPERSEDED. Must not be used.

---

## B. Tables Expected (37 canonical tables)

### Schema: civix

| Migration | Table | Notes |
|---|---|---|
| 001 | *(ENUMs only)* | |
| 002 | `civix_user` | |
| 003 | `source` | |
| 003 | `source_record` | Immutable |
| 003 | `evidence_artifact` | Globally deduplicated |
| 003 | `evidence_instance` | Case-scoped |
| 004 | `entity` | Universal supertype (ADR-001) |
| 004 | `source_identity` | Subtype; raw_identifier immutable |
| 004 | `person` | Subtype; NO is_criminal |
| 004 | `person_alias` | Bitemporal |
| 004 | `phone_number` | Subtype |
| 004 | `sim` | Subtype |
| 004 | `device` | Subtype; IMEI nullable |
| 004 | `vehicle` | Subtype |
| 004 | `property` | Subtype |
| 004 | `financial_account` | Subtype |
| 004 | `organization` | Subtype |
| 004 | `network` | Subtype |
| 004 | `location` | Subtype; PostGIS geometry |
| 005 | `identity_candidate` | |
| 005 | `identity_resolution` | Immutable versioning |
| 005 | `identity_merge_event` | Immutable |
| 005 | `identity_split_event` | Immutable |
| 006 | `sim_number_assignment` | GIST exclusion constraint |
| 006 | `sim_in_device` | GIST exclusion constraint |
| 006 | `account_holder` | Bitemporal |
| 007 | `investigative_case` | Reserved-word safe name |
| 007 | `case_entity_role` | Bitemporal (Gate 3) |
| 007 | `fir` | |
| 007 | `case_access` | Partial unique index (Gate 2) |
| 007 | `case_link` | Cross-case references |
| 008 | `analysis_run` | AI model tracking |
| 008 | `observation` | Immutable |
| 008 | `extraction` | |
| 008 | `event` | No entity FKs (ADR-021) |
| 008 | `event_participant` | N-ary model |
| 008 | `assertion` | No stance; authorized_case_ids (BLK-15) |
| 008 | `hypothesis` | |
| 008 | `hypothesis_support` | Bitemporal (BLK-06) |
| 009 | `investigative_lead` | |
| 009 | `investigation_task` | |
| 010 | `forensic_report` | MVP stub |
| 010 | `medical_report` | MVP stub |
| 011 | `legal_restriction` | |
| 011 | `audit_event` | Append-only (INV-13) |
| 011 | `outbox` | CDC only mechanism (ADR-008) |
| 012 | `provenance` | No DB FKs (ADR-006) |
| 012 | `data_quality_issue` | |
| 013 | `dataset` | |
| 013 | `scenario` | |
| 013 | `generation_run` | |

---

## C. ENUMs Expected (25 types)

| ENUM | Values |
|---|---|
| `entity_type_enum` | PERSON, SOURCE_IDENTITY, PHONE_NUMBER, SIM, DEVICE, FINANCIAL_ACCOUNT, VEHICLE, PROPERTY, ORGANIZATION, NETWORK, LOCATION |
| `source_identity_type_enum` | NAME, PHONE_MSISDN, IMEI, MAC_ADDRESS, VEHICLE_REG, EMAIL, FACE_EMBEDDING_REF, FINGERPRINT_REF, VOICE_PRINT_REF, AADHAAR_MASKED, PAN_MASKED, DRIVING_LICENSE, PASSPORT_NUMBER, OTHER |
| `predicate_enum` | 35 values (CALLED, MESSAGED, PINGED_TOWER…) |
| `participant_role_enum` | CALLER, CALLEE, PING_SOURCE, DRIVER, PASSENGER, REGISTERED_OWNER, SENDER, RECEIVER, ACCOUNT_HOLDER, JOINT_HOLDER, BENEFICIARY, PREVIOUS_OWNER, NEW_OWNER, TARGET_PROPERTY, REGISTRAR, LOCATION, CELL_TOWER, VICTIM, SUSPECT, WITNESS, OFFICER, OBSERVER, SUBJECT, COMPLAINANT, SAMPLE_COLLECTOR, EXAMINER, CUSTODIAN, PARTICIPANT |
| `epistemic_status_enum` | POSSIBLE, PROBABLE, CONFIRMED, REFUTED, INCONCLUSIVE |
| `support_stance_enum` | SUPPORT, CONTRADICT, NEUTRAL, INCONCLUSIVE |
| `identity_resolution_status_enum` | ACCEPTED, REJECTED, SUPERSEDED, UNRESOLVED, REVIEW_REQUIRED |
| `event_type_enum` | CALL, MESSAGE, TRANSACTION, VEHICLE_SIGHTING, PROPERTY_MUTATION, MEETING, SEIZURE, ARREST, SURVEILLANCE_OBSERVATION, FORENSIC_COLLECTION, MEDICAL_EXAMINATION, FIR_FILING, DEVICE_PING, BORDER_CROSSING, OTHER |
| `case_type_enum` | CRIMINAL, INTELLIGENCE, PROPERTY, FINANCIAL, SURVEILLANCE, FORENSIC, MULTI_CASE |
| `case_status_enum` | OPEN, ACTIVE, SUSPENDED, CLOSED_SOLVED, CLOSED_UNSOLVED, ARCHIVED |
| `case_priority_enum` | CRITICAL, HIGH, MEDIUM, LOW |
| `case_entity_role_enum` | SUSPECT, VICTIM, COMPLAINANT, WITNESS, PERSON_OF_INTEREST, ACCUSED, ACQUITTED, OFFICER_IN_CHARGE, INFORMANT, SUBJECT_ORG, SUBJECT_VEHICLE, SUBJECT_ACCOUNT, SUBJECT_PROPERTY, SUBJECT_DEVICE, RELATED_PERSON |
| `civix_role_enum` | INVESTIGATOR, SUPERVISOR, ANALYST, ADMIN, FORENSIC_EXAMINER, LEGAL_OFFICER, READ_ONLY |
| `clearance_enum` | UNCLASSIFIED, RESTRICTED, CONFIDENTIAL, SECRET |
| `case_permission_enum` | READ, WRITE, ADMIN |
| `audit_action_enum` | LOGIN, LOGOUT, READ, WRITE, EXPORT, RESTRICT, LIFT_RESTRICTION, IDENTITY_RESOLVE, HYPOTHESIS_STATUS_CHANGE, LEAD_DISPOSITION, ADMIN_ACTION, TOMBSTONE_ISSUED |
| `legal_restriction_type_enum` | EXPUNGED, SEALED, JUVENILE_PROTECTED, COURT_RESTRICTED, CLASSIFIED, NATIONAL_SECURITY |
| `data_quality_issue_type_enum` | IMPOSSIBLE_TIMESTAMP, MALFORMED_RECORD, DUPLICATE_RECORD, MISSING_REQUIRED_FIELD, CONTRADICTORY_DATA, CUSTODY_GAP, UNKNOWN_IDENTIFIER, HASH_MISMATCH, SPATIAL_IMPOSSIBILITY, TEMPORAL_IMPOSSIBILITY, OTHER |
| `location_type_enum` | EXACT_POINT, ESTIMATED_POINT, CELL_SECTOR_POLYGON, CCTV_COVERAGE_POLYGON, PROPERTY_BOUNDARY, CRIME_SCENE, GEOFENCE, ADMIN_BOUNDARY, ROUTE_LINESTRING |
| `hash_algorithm_enum` | SHA256, SHA512, SHA3_256, MD5_DEPRECATED |
| `extraction_type_enum` | FACE_DETECTION, OCR, ANPR, NER, RELATIONSHIP_EXTRACTION, ANOMALY_DETECTION, CLUSTERING, VOICE_PRINT, FINGERPRINT_MATCH, GEOLOCATION_INFERENCE, TEMPORAL_INFERENCE, OTHER |
| `dataset_type_enum` | GOLDEN_WORLD, SYNTHETIC_TRAIN, SYNTHETIC_VAL, SYNTHETIC_TEST, PRODUCTION |
| `hypothesis_status_enum` | ACTIVE, UNDER_REVIEW, CONFIRMED, REFUTED, ARCHIVED |
| `lead_priority_enum` | CRITICAL, HIGH, MEDIUM, LOW |
| `lead_status_enum` | OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED |
| `task_type_enum` | INTERVIEW, SURVEILLANCE, SEARCH_AND_SEIZURE, FORENSIC_COLLECTION, FINANCIAL_REVIEW, LEGAL_REQUEST, COURT_ORDER, DATA_ANALYSIS, FIELD_VERIFICATION, OTHER |
| `task_status_enum` | PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED |

---

## D. Required Extensions

| Extension | Purpose |
|---|---|
| `postgis` | GEOMETRY types for location, cell sector polygons |
| `uuid-ossp` | `uuid_generate_v4()` function |
| `pgcrypto` | `gen_random_uuid()` alternative |
| `btree_gist` | Required for GIST exclusion constraints on temporal ranges |

---

## E. Bitemporal Tables (tx_start / tx_end mandatory)

| Table | valid_time? | tx_time? | Notes |
|---|---|---|---|
| `source_identity` | YES (observed_at) | YES | |
| `identity_resolution` | NO | YES | Append-only versioning |
| `person_alias` | YES | YES (tx_start only) | |
| `sim_number_assignment` | YES (TSTZRANGE) | YES (tx_start) | |
| `sim_in_device` | YES (TSTZRANGE) | YES (tx_start) | |
| `account_holder` | YES (TSTZRANGE) | YES (tx_start) | |
| `case_access` | YES (valid_until) | YES (tx_start) | Partial unique (BLK-08) |
| `case_entity_role` | YES (valid_from/to) | YES (Gate 3) | |
| `hypothesis_support` | NO | YES (BLK-06) | |
| `assertion` | YES (valid_from/to) | YES (tx_start/end) | |
| `hypothesis` | NO | YES (tx_start/end) | |
| `evidence_instance` | NO | YES (tx_start/end) | |

---

## F. Append-Only Tables (no UPDATE/DELETE ever)

- `source_record` (superseded_by pattern)
- `observation`
- `extraction` (superseded_by pattern)
- `identity_merge_event`
- `identity_split_event`
- `audit_event` (trigger enforced)

---

## G. RLS-Protected Tables

- `evidence_instance` (by case_id)
- `assertion` (by authorized_case_ids — BLK-15)
- `hypothesis` (by case_id)
- `investigative_case` (by case_access)
- `investigative_lead` (by case_id)

---

## H. Polymorphic-Reference Tables (via civix.entity supertype)

- `event_participant` (entity_id → entity)
- `case_entity_role` (entity_id → entity)
- `account_holder` (holder_entity_id → entity)
- `assertion` (subject_entity_id → entity, object_entity_id → entity)

---

## I. Evidence/Provenance Tables

- `evidence_artifact` (global, deduplicated)
- `evidence_instance` (case-scoped)
- `provenance` (no DB FKs — ADR-006)
- `observation` → `extraction` → `event` → `assertion`

---

## J. Outbox/CDC Tables

- `outbox` — Only mechanism for Neo4j sync (ADR-008, INV-20)

---

## K. Temporal Constraints

- `sim_number_assignment`: GIST EXCLUDE `(phone_number_id WITH =, valid_time WITH &&)` — one MSISDN per SIM at a time
- `sim_in_device`: GIST EXCLUDE `(sim_id WITH =, valid_time WITH &&)` — one device per SIM at a time
- `investigative_case`: CHECK `(closed_at IS NULL OR closed_at >= opened_at)`
- `hypothesis`: CHECK `(status != 'CONFIRMED' OR confirmed_by IS NOT NULL)`

---

## L. Required Indexes (Priority Order)

| Index | Table | Columns | Type | Reason |
|---|---|---|---|---|
| idx_entity_type | entity | entity_type | btree | Subtype dispatch |
| idx_source_record_source | source_record | source_id | btree | Provenance joins |
| idx_evidence_hash | evidence_artifact | sha256_hash, hash_algorithm | btree | Deduplication |
| idx_evidence_instance_case | evidence_instance | case_id | btree | RLS |
| idx_evidence_instance_artifact | evidence_instance | artifact_id | btree | GC check |
| idx_assertion_subject | assertion | subject_entity_id | btree | Graph traversal |
| idx_assertion_object | assertion | object_entity_id | btree | Graph traversal |
| idx_assertion_predicate | assertion | predicate | btree | Predicate filtering |
| idx_assertion_tx | assertion | tx_start, tx_end | btree | AS-OF queries |
| idx_assertion_cases | assertion | authorized_case_ids | GIN | RLS array lookup |
| idx_event_type | event | event_type | btree | Event classification |
| idx_event_tx | event | tx_start | btree | Temporal queries |
| idx_eventparticipant_event | event_participant | event_id | btree | N-ary lookups |
| idx_eventparticipant_entity | event_participant | entity_id | btree | Entity event history |
| idx_hypothesis_case | hypothesis | case_id | btree | Case filtering |
| idx_hyp_support_hyp | hypothesis_support | hypothesis_id | btree | Evidence evaluation |
| idx_hyp_support_tx | hypothesis_support | tx_start | btree | AS-OF |
| idx_case_access_user | case_access | user_id | btree | RLS |
| idx_outbox_unconsumed | outbox | consumed_at | btree | CDC consumer |
| idx_sim_number_phone | sim_number_assignment | phone_number_id | btree | Telecom join |
| idx_account_holder_account | account_holder | account_id | btree | Financial queries |
| idx_generation_run | source_record, assertion, event | generation_run_id | btree | Synthetic filtering |

---

## M. Required Triggers

| Trigger | Table | Event | Purpose |
|---|---|---|---|
| `trg_audit_append_only` | `audit_event` | BEFORE UPDATE OR DELETE | Raise exception — immutability |
| `trg_entity_no_delete` | `entity` | BEFORE DELETE | Raise exception — tombstone only (BLK-16) |
| `trg_hypothesis_support_bitemporal` | `hypothesis_support` | BEFORE UPDATE | Close old row, insert new (BLK-17) |
| `trg_case_entity_role_bitemporal` | `case_entity_role` | BEFORE UPDATE | Append-only |
| `trg_outbox_on_assertion_change` | `assertion` | AFTER INSERT OR UPDATE | Emit UPSERT_NODE outbox event |
| `trg_outbox_on_entity_tombstone` | `entity` | AFTER UPDATE (visibility_status) | Emit TOMBSTONE_NODE |
| `trg_assertion_case_ids` | `assertion_evidence` | AFTER INSERT | Append case_id to assertion.authorized_case_ids |

---

## N. Required Foreign Keys

- All subtypes: `entity_id PK REFERENCES civix.entity(entity_id)`
- `evidence_artifact`: `UNIQUE(sha256_hash, hash_algorithm)`
- `evidence_instance`: `artifact_id REFERENCES evidence_artifact(artifact_id)` — implicit DELETE RESTRICT
- `evidence_artifact` (derived): `parent_artifact_id REFERENCES evidence_artifact(artifact_id) ON DELETE RESTRICT`
- `hypothesis_support`: `hypothesis_id`, `assertion_id` both FK
- `event_participant`: `event_id`, `entity_id` both FK

---

## O. Open Decisions (Intentionally Open)

| Decision | Priority |
|---|---|
| CDC consumer technology (Kafka vs Redis vs pg_notify) | DEFERRED to Phase 7 |
| Exact RLS policy expressions — requires production auth stack | DEFERRED to Phase 9 |
| Partitioning strategy (range, hash) | DEFERRED — apply before 10M rows |
| Backend framework (Django, FastAPI) | DEFERRED to Phase 8 |
| Clearance enforcement mechanism | DEFERRED to Phase 9 |

---

## P. Contradictions Discovered

**CONTRADICTION-01 (LOW — resolved by architecture)**:
`case_access` in `03_DATABASE_SCHEMA_BIBLE.md` line 450 still shows `UNIQUE(case_id, user_id)`.
Gate 2 (BLK-08) mandated a PARTIAL unique index: `CREATE UNIQUE INDEX ... WHERE is_revoked = FALSE AND valid_until IS NULL OR valid_until > now()`.
**Resolution**: The migration will implement the partial index, NOT the full UNIQUE constraint. The Bible needs updating in Phase 2 docs (not retroactively edited — reported here per CIVIX_CHANGE_CONTROL.md Rule 4).

**CONTRADICTION-02 (LOW — resolved by Gate 3)**:
`hypothesis_support` in Bible line 522 shows `UNIQUE(hypothesis_id, assertion_id)`.
Gate 3/BLK-06 mandated partial index for bitemporal support.
**Resolution**: Migration implements `UNIQUE INDEX uq_active_support ON hypothesis_support(hypothesis_id, assertion_id) WHERE tx_end IS NULL`.

**CONTRADICTION-03 (INFORMATIONAL)**:
`entity` table in Bible does not list `visibility_status`. BLK-16 mandated tombstoning.
**Resolution**: Migration adds `visibility_status TEXT NOT NULL DEFAULT 'ACTIVE'` to `civix.entity`. Documented here, not silently changed.
