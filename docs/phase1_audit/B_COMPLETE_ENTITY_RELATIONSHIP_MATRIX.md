# B — COMPLETE ENTITY RELATIONSHIP MATRIX
## CIVIX Phase 1 — All Entities, Relationships, and Semantics

**Date**: 2026-08-29 | **Status**: FINAL

> For each entity: Purpose, PK, FKs, Cardinality, Temporal semantics, Provenance, Security, Mutability.
> **Mutability**: IMMUTABLE | MUTABLE | APPEND-ONLY | SUPERSEDE-ONLY
> **Status**: CANONICAL (source of truth) | ANALYTICAL (derived/projection) | OPERATIONAL

---

## GROUP 1: Infrastructure

### `civix.entity` — Universal Entity Supertype
| Property | Value |
|---|---|
| Purpose | Shared PK root for all domain entities |
| PK | `entity_id UUID` |
| FKs | `created_by → civix_user (nullable)` |
| Parent | None |
| Children | person, source_identity, phone_number, sim, device, vehicle, property, financial_account, organization, network, location |
| Cardinality | 1:1 with each subtype |
| Temporal | `created_at TIMESTAMPTZ` (monotonic) |
| Provenance | `created_by` |
| Security | Case-level access via subtype |
| Mutability | APPEND-ONLY (rows never deleted or updated) |
| Status | CANONICAL |

### `civix.civix_user`
| Property | Value |
|---|---|
| Purpose | CIVIX investigative identity (NOT authentication) |
| PK | `user_id UUID` |
| FKs | None |
| Parent | None |
| Children | audit_event, case_access, identity_resolution |
| Cardinality | N/A |
| Temporal | `created_at`, `last_login_at` |
| Provenance | External auth provider via `external_auth_id` |
| Security | Admin-only management |
| Mutability | MUTABLE (role, clearance may change) |
| Status | OPERATIONAL |
| **GAPS** | No `tx_start/tx_end` for role history. BLK-09 pending. |

---

## GROUP 2: Source & Evidence

### `civix.source`
| Property | Value |
|---|---|
| Purpose | External agency that provided data |
| PK | `source_id UUID` |
| FKs | `source_handler_id → civix_user (nullable)` |
| Children | source_record |
| Cardinality | 1:N to source_record |
| Temporal | `created_at` only |
| Provenance | `source_handler_id` for protected sources |
| Security | `is_identity_protected` requires ADMIN/handler to see source name |
| Mutability | MUTABLE (reliability_score may change) |
| Status | CANONICAL |
| **GAPS** | GAP-51: `classification_level` field missing. GAP-42: `agency_type` should be ENUM. |

### `civix.source_record`
| Property | Value |
|---|---|
| Purpose | Immutable receipt of one data payload from a source |
| PK | `source_record_id UUID` |
| FKs | `source_id → source`, `superseded_by → self (nullable)`, `generation_run_id → generation_run (nullable)` |
| Parent | source |
| Children | evidence_artifact, evidence_instance, observation, source_identity, event |
| Cardinality | N:1 to source; 1:N to evidence_instance |
| Temporal | `received_at TIMESTAMPTZ` (transaction time) |
| Provenance | Full — source_id is the provenance anchor |
| Security | Inherits source's classification |
| Mutability | SUPERSEDE-ONLY (never UPDATE; corrections create new row + set superseded_by) |
| Status | CANONICAL |

### `civix.evidence_artifact`
| Property | Value |
|---|---|
| Purpose | Deduplicated binary artifact (file) |
| PK | `artifact_id UUID` |
| FKs | None (self-contained) |
| Children | evidence_instance |
| Cardinality | 1:N to evidence_instance |
| Unique | `UNIQUE(sha256_hash, hash_algorithm)` — ADR-004 |
| Temporal | `acquired_at`, `created_at` |
| Provenance | Content hash is the provenance identity |
| Security | RLS via evidence_instance.case_id |
| Mutability | IMMUTABLE (file content never changes; integrity preserved by hash) |
| Status | CANONICAL |
| **GAPS** | GAP-51: No `classification_level`. BLK-11. GAP-40: No structured CCTV metadata. BLK-11. |

### `civix.evidence_instance`
| Property | Value |
|---|---|
| Purpose | Case-scoped context for an artifact |
| PK | `instance_id UUID` |
| FKs | `artifact_id → evidence_artifact`, `case_id → investigative_case NOT NULL`, `source_record_id → source_record`, `acquired_by → civix_user` |
| Parent | evidence_artifact, investigative_case |
| Children | observation, forensic_report, medical_report |
| Cardinality | N:1 to artifact; N:1 to case |
| Temporal | Bitemporal: `tx_start/tx_end` |
| Provenance | `acquired_by`, `acquisition_method` |
| Security | RLS on `case_id` |
| Mutability | MUTABLE for legal_status changes; tx_end for soft-delete |
| Status | CANONICAL |
| **GAPS** | BLK-07: requires pre-existing case. GAP-22: `legal_status` should be ENUM. |

---

## GROUP 3: Identity

### `civix.source_identity`
| Property | Value |
|---|---|
| Purpose | Raw identifier as it appeared in source data |
| PK | `entity_id UUID (FK→entity)` |
| FKs | `entity_id → entity`, `source_record_id → source_record`, `extraction_id → extraction` |
| Parent | entity, source_record |
| Children | identity_candidate |
| Cardinality | N:1 to source_record |
| Temporal | Bitemporal: `observed_at (valid_time)`, `tx_start/tx_end` |
| Provenance | `source_record_id` for raw; `extraction_id` for AI-derived |
| Security | Inherits entity security |
| Mutability | IMMUTABLE (`raw_identifier` never changes; INV-03) |
| Status | CANONICAL |
| **GAPS** | BLK-03: `extraction_id` contradicts ADR-006. GAP-29: No trigger enforcing raw_identifier immutability. |

### `civix.person`
| Property | Value |
|---|---|
| Purpose | Canonical, resolved real-world person |
| PK | `entity_id UUID (FK→entity)` |
| FKs | `entity_id → entity` |
| Parent | entity |
| Children | person_alias, identity_candidate, case_entity_role, observation |
| Cardinality | 1:N to aliases, candidates |
| Temporal | `date_of_birth DATE`, `deceased_at DATE` |
| Provenance | Created via identity_resolution |
| Security | Case-level; `legal_restriction` for juvenile/expunge |
| Mutability | MUTABLE (display_name, is_deceased may change) |
| Status | CANONICAL |
| **INVARIANTS** | INV-07: Person never auto-created from SourceIdentity. INV-17: No is_criminal field. |

### `civix.identity_candidate`
| Property | Value |
|---|---|
| Purpose | AI-proposed link between SourceIdentity and Person |
| PK | `candidate_id UUID` |
| FKs | `source_identity_id → source_identity`, `proposed_person_id → person`, `analysis_run_id → analysis_run` |
| Unique | `UNIQUE(source_identity_id, proposed_person_id)` |
| Cardinality | N:1 to source_identity; N:1 to person |
| Temporal | `created_at` only |
| Provenance | `analysis_run_id` |
| Security | Sensitive — case-adjacent |
| Mutability | MUTABLE (`is_active` changes when accepted/rejected) |
| Status | ANALYTICAL |
| **GAPS** | ADV-21: After rejection, cannot re-propose same pair due to UNIQUE constraint. |

### `civix.identity_resolution`
| Property | Value |
|---|---|
| Purpose | Human decision on an identity_candidate |
| PK | `resolution_id UUID` |
| FKs | `source_identity_id → source_identity`, `candidate_id → identity_candidate`, `resolved_person_id → person`, `decided_by → civix_user`, `superseded_by → self` |
| Constraint | `CHECK (status != 'ACCEPTED' OR resolved_person_id IS NOT NULL)` |
| Temporal | Bitemporal: `tx_start/tx_end` |
| Provenance | `decided_by` |
| Security | Restricted to investigators and above |
| Mutability | SUPERSEDE-ONLY |
| Status | CANONICAL |

### `civix.identity_merge_event`
| Property | Value |
|---|---|
| Purpose | Audit trail for merging two SourceIdentities into one Person |
| PK | `merge_event_id UUID` |
| FKs | `source_identity_a/b → source_identity`, `merged_into_person_id → person`, `resolution_id → identity_resolution`, `decided_by → civix_user` |
| Temporal | `occurred_at TIMESTAMPTZ` |
| Provenance | `decided_by` |
| Mutability | IMMUTABLE |
| Status | CANONICAL |

### `civix.identity_split_event`
| Property | Value |
|---|---|
| Purpose | Audit trail for splitting a merged identity |
| PK | `split_event_id UUID` |
| FKs | `original_resolution_id → identity_resolution`, `split_source_identity_a/b → source_identity`, `new_person_b_id → person`, `decided_by → civix_user` |
| Temporal | `occurred_at TIMESTAMPTZ` |
| Provenance | `decided_by` |
| Mutability | IMMUTABLE |
| Status | CANONICAL |

---

## GROUP 4: Domain Entities (Subtypes of `entity`)

### `civix.phone_number`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Unique | `msisdn VARCHAR(15) UNIQUE` |
| Children | sim_number_assignment |
| Temporal | No entity-level temporal; use sim_number_assignment for time |
| **GAPS** | `number_type TEXT` should be ENUM. |

### `civix.sim`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Unique | `iccid VARCHAR(22) UNIQUE`, `imsi UNIQUE NULL` |
| Children | sim_number_assignment, sim_in_device |
| **GAPS** | GAP-59: No SIM cardinality in golden world. GAP-53: No SIM dataclass in models.py. |

### `civix.device`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Unique | `imei UNIQUE NULL`, `mac_address UNIQUE NULL` (both nullable for UNKNOWN-IMEI) |
| Children | sim_in_device |
| **GAPS** | `device_type TEXT` should be ENUM. |

### `civix.vehicle`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Unique | `registration_number TEXT UNIQUE`, `vin UNIQUE NULL` |
| Children | event_participant (via entity) |
| **GAPS** | GAP-50: `models.py Vehicle.entity_id` means owner, not vehicle entity. Ingestion mapping must be documented. |

### `civix.property`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Fields | `property_ref TEXT NOT NULL`, `property_type TEXT NOT NULL`, `boundary_geometry GEOMETRY(Polygon)` |
| Children | event_participant (via entity) |
| Relationship | Via assertion: `OWNED` / `TRANSFERRED_OWNERSHIP_OF` / `RECEIVED_PROPERTY` |
| **GAPS** | `property_type TEXT` should be ENUM. |

### `civix.financial_account`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Fields | `masked_number TEXT NOT NULL`, `account_type TEXT NOT NULL` |
| Children | account_holder |
| **GAPS** | `account_type TEXT` should be ENUM (SAVINGS, CURRENT, CREDIT, LOAN). |

### `civix.organization`
| PK | `entity_id (FK→entity)` |
| Fields | `legal_name TEXT NOT NULL`, `org_type TEXT NOT NULL` |
| **GAPS** | `org_type TEXT` should be ENUM. |

### `civix.network`
| PK | `entity_id (FK→entity)` |
| Fields | `network_name TEXT NOT NULL`, `network_type TEXT NOT NULL` |
| **INVARIANT** | INV-16: network_type='CRIMINAL' is investigative, NOT proof of guilt |

### `civix.location`
| Property | Value |
|---|---|
| PK | `entity_id (FK→entity)` |
| Fields | `geometry GEOMETRY NOT NULL`, `location_type location_type_enum NOT NULL`, `uncertainty_radius_meters FLOAT NULL`, `azimuth_degrees FLOAT NULL`, `beamwidth_degrees FLOAT NULL` |
| **INVARIANT** | INV-19: Cell tower centroid ≠ user location. ADR-009. |
| **GAPS** | BLK-05: LOC-* coordinates undefined for Golden World. |

---

## GROUP 5: Telecom Relationships

### `civix.sim_number_assignment`
| Property | Value |
|---|---|
| Purpose | Which SIM had which MSISDN at which time |
| PK | `assignment_id UUID` |
| FKs | `sim_id → sim`, `phone_number_id → phone_number` |
| Constraint | `EXCLUDE USING GIST (phone_number_id WITH =, valid_time WITH &&)` — phone number cannot be on two SIMs simultaneously |
| Temporal | `valid_time TSTZRANGE NOT NULL`, `tx_start` |
| Mutability | SUPERSEDE-ONLY |

### `civix.sim_in_device`
| Property | Value |
|---|---|
| Purpose | Physical tracking of SIM in device |
| PK | `id UUID` |
| FKs | `sim_id → sim`, `device_id → device` |
| Constraint | `EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&)` — physical law: one SIM, one device at a time |
| Temporal | `valid_time TSTZRANGE NOT NULL`, `tx_start` |
| **Note** | Human-use overlap (two people sharing device) is NOT constrained here |

---

## GROUP 6: Finance

### `civix.account_holder`
| Property | Value |
|---|---|
| Purpose | Person's role in a financial account over time |
| PK | `holder_id UUID` |
| FKs | `account_id → financial_account`, `holder_entity_id → entity` |
| Temporal | `valid_time TSTZRANGE NOT NULL`, `tx_start` |
| **GAPS** | `holder_role TEXT` should be `account_holder_role_enum` |

---

## GROUP 7: Cases & Workflow

### `civix.investigative_case`
| Property | Value |
|---|---|
| Purpose | Formal investigative case |
| PK | `case_id UUID` |
| FKs | `lead_investigator_id → civix_user` |
| Children | hypothesis, investigative_lead, investigation_task, evidence_instance, case_access, fir, case_entity_role, case_link |
| Temporal | `opened_at DATE`, `closed_at DATE` |
| Constraint | `CHECK (closed_at IS NULL OR closed_at >= opened_at)` |
| Mutability | MUTABLE (status, priority, closed_at) |
| Note | Named `investigative_case` not `case` — ADR-003 |

### `civix.case_access`
| Property | Value |
|---|---|
| Purpose | Per-user permission on a case |
| PK | `access_id UUID` |
| FKs | `case_id → investigative_case`, `user_id → civix_user`, `granted_by → civix_user` |
| Unique | `UNIQUE(case_id, user_id)` — **BLK-08 pending fix** |
| Temporal | `granted_at`, `valid_until`, `revoked_at` |
| **GAPS** | BLK-08: UNIQUE prevents permission level history. Fix: partial unique index WHERE is_revoked=FALSE. |

### `civix.case_entity_role`
| Property | Value |
|---|---|
| Purpose | A person/entity's role within a specific case |
| PK | `role_id UUID` |
| FKs | `case_id → investigative_case`, `entity_id → entity`, `assigned_by → civix_user` |
| Unique | `UNIQUE(case_id, entity_id, role)` |
| Temporal | `valid_from DATE NULL`, `valid_to DATE NULL` |
| **GAPS** | BLK-18: DATE should be TIMESTAMPTZ; need tx_start/tx_end. |

### `civix.hypothesis`
| Property | Value |
|---|---|
| Purpose | An investigative theory under evaluation |
| PK | `hypothesis_id UUID` |
| FKs | `case_id → investigative_case`, `created_by → civix_user`, `confirmed_by → civix_user` |
| Constraint | `CHECK (status != 'CONFIRMED' OR confirmed_by IS NOT NULL)` — AI cannot self-confirm |
| Children | hypothesis_support |
| Temporal | Bitemporal: `tx_start/tx_end` |
| Mutability | MUTABLE (status changes) |
| **GAPS** | BLK-01: `hypothesis_status_enum` not defined. |

### `civix.hypothesis_support`
| Property | Value |
|---|---|
| Purpose | Directional relationship: does assertion A support hypothesis H? |
| PK | `support_id UUID` |
| FKs | `hypothesis_id → hypothesis`, `assertion_id → assertion`, `assigned_by → civix_user`, `analysis_run_id → analysis_run` |
| Unique | `UNIQUE(hypothesis_id, assertion_id)` — **BLK-06 pending fix** |
| Constraint | stance ∈ support_stance_enum |
| **GAPS** | BLK-06: No tx_start/tx_end; no bitemporal stance versioning. BLK-04: CONTRADICT graph projection issue. |

### `civix.investigative_lead`
| Property | Value |
|---|---|
| Purpose | Actionable tip from hypothesis evaluation |
| PK | `lead_id UUID` |
| FKs | `case_id → investigative_case`, `generated_by_run_id → analysis_run`, `generated_by_person → civix_user`, `disposed_by → civix_user` |
| Constraint | `CHECK (generated_by_run_id IS NOT NULL OR generated_by_person IS NOT NULL)` |
| Children | investigation_task |
| **GAPS** | BLK-01: `lead_priority_enum`, `lead_status_enum` not defined. BLK-10: lead_text may contain PII of expunged entities. |

### `civix.investigation_task`
| Property | Value |
|---|---|
| Purpose | Specific human action to perform |
| PK | `task_id UUID` |
| FKs | `lead_id → investigative_lead (nullable)`, `case_id → investigative_case`, `assigned_to → civix_user` |
| **GAPS** | BLK-01: `task_type_enum`, `task_status_enum` not defined. |

---

## GROUP 8: Epistemic Pipeline

### `civix.analysis_run`
| Property | Value |
|---|---|
| Purpose | An AI/ML model run that produces extractions and assertions |
| PK | `run_id UUID` |
| Fields | `model_name, model_version, algorithm_type, algorithm_parameters JSONB, input_snapshot_hash, input_snapshot_tx_time` |
| Children | extraction, assertion, investigative_lead, identity_candidate |
| Temporal | `started_at, finished_at` |
| **GAPS** | ADV-22: No `status` or `is_voided` field — cannot mark a run as faulty. |

### `civix.observation`
| Property | Value |
|---|---|
| Purpose | Directly recorded fact from evidence |
| PK | `observation_id UUID` |
| FKs | `instance_id → evidence_instance`, `observed_by → civix_user (nullable)` |
| Temporal | `observed_at TIMESTAMPTZ (valid time)`, `tx_start (transaction time)` |
| Mutability | IMMUTABLE (corrections create new rows) |
| **GAPS** | BLK-13: `observed_by → civix_user` conflicts with field-officer observers who are Persons not users. Proposed: add `observer_entity_id → entity`. FINDING-16: `observer_type` and `observation_type` should be ENUMs. |

### `civix.extraction`
| Property | Value |
|---|---|
| Purpose | AI/ML-derived inference from evidence |
| PK | `extraction_id UUID` |
| FKs | `instance_id → evidence_instance`, `analysis_run_id → analysis_run`, `superseded_by → self` |
| Fields | `ai_confidence DECIMAL(5,4) CHECK 0-1`, `extracted_value JSONB`, `is_superseded BOOL` |
| Temporal | `tx_start` |
| Mutability | SUPERSEDE-ONLY |

### `civix.event`
| Property | Value |
|---|---|
| Purpose | A real-world occurrence hub |
| PK | `event_id UUID` |
| FKs | `source_record_id → source_record (nullable)`, `generation_run_id → generation_run (nullable)` |
| **CRITICAL**: No entity FKs — all entity relationships go via event_participant |
| Children | event_participant |
| Temporal | `occurred_at TSTZRANGE NOT NULL` (real-world time interval, not scalar) |
| Mutability | IMMUTABLE (events are facts) |
| **GAPS** | FINDING-10: No FK to observation. Linkage via provenance table. Must be documented explicitly. |

### `civix.event_participant`
| Property | Value |
|---|---|
| Purpose | N-ary event participation record |
| PK | `participant_id UUID` |
| FKs | `event_id → event`, `entity_id → entity` |
| Unique | `UNIQUE(event_id, entity_id, participant_role)` |
| Fields | `participant_role participant_role_enum NOT NULL`, `role_confidence DECIMAL NULL` |
| Temporal | `tx_start` |
| Mutability | IMMUTABLE |

### `civix.assertion`
| Property | Value |
|---|---|
| Purpose | A structured S-P-O claim about the world |
| PK | `assertion_id UUID` |
| FKs | `subject_entity_id → entity NOT NULL`, `object_entity_id → entity NULL`, `object_location_id → location NULL (REDUNDANT — see BLK-17)`, `asserted_by → civix_user NULL`, `source_analysis_run_id → analysis_run NULL` |
| Constraint | At least one object column must be non-NULL |
| Constraint | `CHECK (asserted_by IS NOT NULL OR source_analysis_run_id IS NOT NULL)` |
| Temporal | Bitemporal: `valid_from/valid_to` (real world), `tx_start/tx_end` (system time) |
| **INVARIANT** | INV-01: No stance. INV-18: predicate from predicate_enum only. |
| **GAPS** | BLK-17: `object_location_id` redundant. ADV-19: No case_id — cross-case assertion access is ungated. ADV-22: No supersession mechanism on assertion itself. GAP-09: Predicate-to-valid-object-type constraints missing. |

---

## GROUP 9: Security & Legal

### `civix.legal_restriction`
| Property | Value |
|---|---|
| Purpose | Court-ordered or legal restriction on an entity or artifact |
| PK | `restriction_id UUID` |
| FKs | `target_entity_id → entity NULL`, `target_artifact_id → evidence_artifact NULL`, `created_by → civix_user`, `lifted_by → civix_user NULL` |
| Constraint | `CHECK (target_entity_id IS NOT NULL OR target_artifact_id IS NOT NULL)` |
| Temporal | `effective_range TSTZRANGE NOT NULL` |
| **GAPS** | `scope TEXT`, `status TEXT` should be ENUMs. BLK-15. |

### `civix.audit_event`
| Property | Value |
|---|---|
| Purpose | Immutable audit log |
| PK | `audit_id UUID` |
| FKs | `user_id → civix_user`, `case_context_id → investigative_case NULL` |
| Temporal | `timestamp TIMESTAMPTZ NOT NULL` |
| Mutability | APPEND-ONLY (trigger prevents UPDATE/DELETE) |
| **INVARIANT** | INV-13 |

### `civix.outbox`
| Property | Value |
|---|---|
| Purpose | Neo4j synchronization queue |
| PK | `id UUID` |
| Fields | `entity_id UUID NOT NULL`, `action TEXT (UPSERT/DELETE/TOMBSTONE)`, `entity_type TEXT`, `payload JSONB`, `created_at`, `consumed_at NULL` |
| **INVARIANT** | INV-20: Only mechanism for Neo4j changes |

---

## GROUP 10: Provenance & Data Quality

### `civix.provenance`
| Property | Value |
|---|---|
| Purpose | Cross-entity lineage graph |
| PK | `provenance_id UUID` |
| Fields | `derived_type TEXT`, `derived_id UUID`, `source_type TEXT`, `source_id UUID`, `derivation_method TEXT` |
| **NO DB FKs** — application-enforced per ADR-006 |
| **CRITICAL GAPS** | BLK-16: No compound index on `(derived_id, derived_type)` and `(source_id, source_type)`. Performance blocker. |

### `civix.data_quality_issue`
| Property | Value |
|---|---|
| Purpose | Captures detected data quality problems |
| PK | `issue_id UUID` |
| Fields | `issue_type data_quality_issue_type_enum`, `severity TEXT (→ ENUM pending)`, `status TEXT` |
| **NO FK** to affected entity (polymorphic) |
| **GAPS** | `severity TEXT` should be ENUM. BLK-15. |

---

## GROUP 11: Synthetic Data Control

### `civix.dataset`, `civix.scenario`, `civix.generation_run`
| Property | Value |
|---|---|
| Purpose | Tag all synthetic rows; isolate production from training data |
| Key relationship | All synthetic rows in operational tables carry `generation_run_id FK` |
| ML pipeline rule | `WHERE generation_run_id IS NULL` selects production-only data |
| **INVARIANT** | INV-14: `scenario.ground_truth` NEVER projected to Neo4j |
| **GAPS** | BLK-02: `output/ground_truth.json` is empty. |

---

## Relationship Matrix Summary

| From → To | Relationship | Cardinality | Temporal | Notes |
|---|---|---|---|---|
| source → source_record | HAS_RECORD | 1:N | received_at | Immutable chain |
| source_record → evidence_artifact | PRODUCES | 1:N | — | Via hash dedup |
| evidence_artifact → evidence_instance | APPEARS_IN | 1:N | tx_start/tx_end | Per-case scoping |
| evidence_instance → observation | OBSERVED_IN | 1:N | observed_at | Immutable |
| evidence_instance → extraction | EXTRACTED_FROM | 1:N | tx_start | Supersedable |
| observation/extraction → event | PRODUCES (provenance) | N:M | occurred_at | Via provenance table, no FK |
| event → event_participant | HAS_PARTICIPANT | 1:N | tx_start | N-ary |
| event_participant → entity | PARTICIPATED_AS | N:1 | — | Any entity type |
| entity → assertion (subject) | SUBJECT_OF | 1:N | valid_from/to | Any entity |
| entity → assertion (object) | OBJECT_OF | 1:N | valid_from/to | Any entity |
| assertion → hypothesis_support | EVALUATED_BY | 1:N | tx_start (pending BLK-06) | Multi-hypothesis |
| hypothesis_support → hypothesis | SUPPORTS/CONTRADICTS | N:1 | stance | ADR-002 |
| hypothesis → investigative_lead | GENERATES | 1:N | created_at | Human/AI-generated |
| investigative_lead → investigation_task | HAS_TASK | 1:N | due_date | Human action |
| source_identity → identity_candidate | PROPOSES | 1:N | created_at | AI proposals |
| identity_candidate → person | RESOLVES_TO | N:1 | resolution.tx_start | Human decision |
| entity → legal_restriction | RESTRICTS | N:1 | effective_range | TSTZRANGE |
| entity/artifact → outbox | SYNC_TRIGGER | — | created_at | INV-20 |
| any → provenance | DERIVED_FROM | N:N | created_at | App-enforced FKs |
