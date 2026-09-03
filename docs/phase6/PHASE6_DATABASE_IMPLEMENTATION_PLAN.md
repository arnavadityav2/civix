# Phase 6: Database Implementation Plan

**Date**: 2026-08-30
**Status**: APPROVED FOR IMPLEMENTATION

---

## Architecture Corrections After Pre-Migration Audit

Following a rigorous pre-migration consistency audit, the following architectural ambiguities were explicitly resolved. (For full rationale, see `PHASE6_PRE_MIGRATION_DECISION_LOG.md`).

1. **GiST Temporal Exclusion (`btree_gist`)**: The `btree_gist` extension will be explicitly installed in `001_extensions.py` to support scalar `UUID` equality inside GiST exclusion constraints.
2. **UUID Strategy**: Standardizes exclusively on PostgreSQL 13+'s native `gen_random_uuid()`. `uuid-ossp` is rejected.
3. **Entity Subtype Integrity**: Subtype tables will enforce integrity via a composite discriminator `UNIQUE(entity_id, entity_type)` and `CHECK(entity_type='TYPE')`.
4. **Row-Level Security (RLS) Architecture**: 
   - Policies use `current_setting('civix.current_user_id', true)` so missing settings securely fail closed (returning NULL instead of throwing errors).
   - Application transactions must use `SET LOCAL civix.current_user_id = '...';` so identity does not bleed across connection pools.
   - Explicit `WITH CHECK` clauses mirror `USING` clauses.
   - `FORCE ROW LEVEL SECURITY` is mandated.
5. **Role Credential Security**: Alembic migrations will NOT embed plain-text passwords (`CREATE ROLE ... WITH LOGIN PASSWORD`). Role provisioning and secret injection is delegated to deployment bootstrap scripts/environment management.
6. **Synthetic Metadata vs Ground Truth**: 
   - `dataset` = dataset-level metadata.
   - `scenario` = scenario/generation configuration metadata.
   - `generation_run` = execution/provenance metadata.
   - NONE of these tables stores per-entity synthetic ground-truth labels (e.g., `is_criminal`, `fraudulent_buyer_id`). Ground truth remains completely isolated in the synthetic dataset artifact layer.
7. **Deletion & Redaction (Tightened Scope)**:
   - **Immutable**: Always blocked from deletion (`audit_event`, `source_record`, `evidence_artifact`, `identity_merge_event`, `identity_resolution`, `identity_split_event`, `legal_restriction`, `provenance`).
   - **Synthetic-Deletable Operational Tables**: `DELETE` is permitted ONLY when `generation_run_id IS NOT NULL` (`person`, `device`, `hypothesis`, etc.).
   - **System/Lifecycle**: Explicitly defined semantics (e.g., `outbox` records are consumed and deleted by CDC).

---

## 1. Confirmed Architectural Decisions

- **Canonical Migration Tool**: Alembic (using SQLAlchemy Core constructs).
- **Forensic MVP Stubs**: `medical_report` and `forensic_report` included as minimal MVP stubs.

---

## 2. Complete Proposed PostgreSQL Entity Inventory (Canonical schema: 50 tables)

- **Auth & Source Data**: `civix_user`, `source`, `source_record`, `evidence_artifact`, `evidence_instance`
- **Core Entities**: `entity`, `person`, `source_identity`, `phone_number`, `sim`, `device`, `financial_account`, `vehicle`, `property`, `organization`, `network`, `location`
- **Identity Resolution**: `person_alias`, `identity_candidate`, `identity_resolution`, `identity_merge_event`, `identity_split_event`
- **Domain Constraints**: `sim_number_assignment`, `sim_in_device`, `account_holder`
- **Case Management**: `investigative_case`, `case_entity_role`, `fir`, `case_access`, `case_link`
- **Epistemic Pipeline**: `analysis_run`, `observation`, `extraction`, `event`, `event_participant`, `assertion`, `hypothesis`, `hypothesis_support`
- **Investigative Workflow**: `investigative_lead`, `investigation_task`
- **Forensic MVP**: `forensic_report`, `medical_report`
- **System, Legal, & Data Quality**: `legal_restriction`, `audit_event`, `outbox`, `provenance`, `data_quality_issue`
- **Synthetic Data Control (Metadata Only)**: `dataset`, `scenario`, `generation_run`

---

## 3. RLS Table-by-Table Matrix

Before `009_security_audit.py` generates policies, the case-scoping paths are strictly defined:

| Table | Case Scope | RLS Mechanism (Path to `case_access`) |
|-------|------------|---------------------------------------|
| `investigative_case` | Direct | `WHERE case_id = investigative_case.case_id` |
| `case_entity_role` | Direct | `WHERE case_id = case_entity_role.case_id` |
| `evidence_instance` | Direct | `WHERE case_id = evidence_instance.case_id` |
| `hypothesis` | Direct | `WHERE case_id = hypothesis.case_id` |
| `hypothesis_support` | Indirect | `JOIN hypothesis h ON h.hypothesis_id = hypothesis_support.hypothesis_id WHERE h.case_id = ...` |
| `medical_report` | Indirect | `JOIN evidence_instance e ON e.instance_id = medical_report.instance_id WHERE e.case_id = ...` |
| `forensic_report` | Indirect | `JOIN evidence_instance e ON e.instance_id = forensic_report.instance_id WHERE e.case_id = ...` |
| `observation` / `extraction` | Indirect | `JOIN evidence_instance e ON e.instance_id = child.instance_id WHERE e.case_id = ...` |
| `entity` / `person` / `event` | Global Reality | Read-only globally (subject to `legal_restriction`). Suspicion/evidence linking them is strictly case-scoped via `case_entity_role` or `assertion`. |

---

## 4. Entity-by-Entity Purpose (Core Subsystem)

- **entity**: The universal supertype with `entity_type` discriminator.
- **source_identity**: Immutable raw identifier. Anchor for ingestion.
- **person**: The canonical human being.
- **event** & **event_participant**: Models real-world occurrences. Entities participate in events.
- **assertion**: A structured claim about an entity.
- **hypothesis** & **hypothesis_support**: Investigators group assertions under a hypothesis, assigning a stance (`SUPPORT`, `CONTRADICT`).

---

## 5. Primary Keys and Foreign Keys

- **Primary Keys**: 100% of tables use native `UUID` (`gen_random_uuid()`).
- **Subtype Integrity**: Entity subtypes use a composite Foreign Key referencing `entity (entity_id, entity_type)` to guarantee polymorphic integrity.

---

## 6. Identity Strategy

- Government and operational identifiers are **never** Primary Keys.
- Modeled exclusively as `source_identity` rows with a typed enum.
- Resolved to a `person` via `identity_resolution`.

---

## 7. Case / Evidence / Entity-Role Architecture

- Criminality is a temporal, legal hypothesis, not a structural boolean.
- No `is_criminal` flags exist on `person`.
- Suspicion is mapped via `case_entity_role`.

---

## 8. Audit / Provenance Requirements

- **Immutable/Audit Tables**: Triggers completely block `DELETE` and `UPDATE` on `audit_event`, `source_record`, `evidence_artifact`, `identity_merge_event`, `identity_resolution`, `identity_split_event`, `legal_restriction`, and `provenance`.
- **Synthetic-Deletable Operational Tables**: Triggers block `DELETE` unless `generation_run_id IS NOT NULL`.
- **System Lifecycle Tables**: `outbox` records are consumed/deleted by external CDC workers.

---

## 9. Required Indexes and Constraints

- **Bitemporal Exclusions**: `sim_number_assignment` uses `EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&)`.
- **Composite Uniqueness**: `evidence_artifact` enforces `UNIQUE(sha256_hash, hash_algorithm)`.
- **RLS Enforcements**: `ALTER TABLE tablename ENABLE ROW LEVEL SECURITY;` and `FORCE ROW LEVEL SECURITY;`.

---

## 10. Neo4j Projection Boundaries

- **Allowed**: Projecting entities, events, locations, and supporting assertions.
- **Forbidden**: Projecting audit logs, system metadata, or synthetic ground-truth definitions.
- **Structural Safety**: Graph algorithms exclude `[:HAS_STANCE]` where stance is `CONTRADICT`.

---

## 11. Alembic Migration Structure

- `alembic/versions/001_extensions.py` (postgis, btree_gist)
- `alembic/versions/002_enums.py`
- `alembic/versions/003_auth_source.py` (Creates role shell, no plain-text credentials)
- `alembic/versions/004_entities.py`
- `alembic/versions/005_relationships.py`
- `alembic/versions/006_cases_evidence.py`
- `alembic/versions/007_epistemic.py`
- `alembic/versions/008_workflow_forensics.py`
- `alembic/versions/009_security_audit.py`

---

## 12. Explicit Statement of What Will NOT Be Implemented Yet

During Phase 6 execution, I will **NOT**:
- Modify the synthetic Parquet datasets in `D:\civix_data\`.
- Modify the Phase 5 ML artifacts (`.json`, `.pkl`).
- Retrain any models.
- Write any Neo4j Cypher queries or CDC consumers.
- Start a FastAPI backend.
- Execute destructive operations on operational data.

---

# FINAL VERDICT

## PHASE 6 PRE-MIGRATION ARCHITECTURE: READY
The implementation plan natively enforces the corrected architectures (RLS session security, strict immutable/synthetic deletion boundaries, explicit RLS table matrices, and credential isolation). The Alembic framework is ready for initialization.
