# 19 — Implementation Master Plan
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: LIVE — Execution begins at Phase 1

> [!IMPORTANT]
> Do not start a phase until its prerequisites are complete and its exit gate is met.
> Record every material implementation decision in `CIVIX_CHANGE_CONTROL.md`.
> Do not modify frozen artifacts during any phase.

---

## Phase 0 — Documentation & Context Lock

**Objective**: Establish permanent documentation so that any future agent or engineer can onboard without relying on chat history.

**Status**: ✅ COMPLETE

**Deliverables**:
- [x] `docs/CIVIX_CONTEXT_INDEX.md`
- [x] `docs/CIVIX_CHANGE_CONTROL.md`
- [x] `docs/00_CIVIX_MASTER_CONTEXT.md`
- [x] `docs/01_PROJECT_VISION.md`
- [x] `docs/02_SYSTEM_ARCHITECTURE_BIBLE.md`
- [x] `docs/03_DATABASE_SCHEMA_BIBLE.md`
- [x] `docs/04_DATA_MODEL_AND_ONTOLOGY.md`
- [x] `docs/05_EPISTEMIC_MODEL.md`
- [x] `docs/06_IDENTITY_RESOLUTION_BIBLE.md`
- [x] `docs/07_FORENSICS_AND_MEDICAL_BIBLE.md`
- [x] `docs/08_SPATIOTEMPORAL_MODEL.md`
- [x] `docs/09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md`
- [x] `docs/10_SECURITY_RBAC_AUDIT_BIBLE.md`
- [x] `docs/11_AI_ML_BIBLE.md`
- [x] `docs/12_SYNTHETIC_DATA_BIBLE.md`
- [x] `docs/13_NEO4J_GRAPH_BIBLE.md`
- [x] `docs/14_POSTGRESQL_BIBLE.md`
- [x] `docs/15_API_BACKEND_BIBLE.md`
- [x] `docs/16_FRONTEND_BIBLE.md`
- [x] `docs/17_LEGAL_COMPLIANCE_BIBLE.md`
- [x] `docs/18_TESTING_VALIDATION_BIBLE.md`
- [x] `docs/19_IMPLEMENTATION_MASTER_PLAN.md` (this file)
- [x] `docs/20_DECISIONS_AND_CHANGELOG.md`
- [x] `docs/21_KNOWN_GAPS_AND_RISKS.md`

**Exit gate**: All 23 documentation files exist and `CIVIX_CONTEXT_INDEX.md` correctly references all of them.

---

## Phase 1 — Architecture Reconciliation

**Objective**: Verify that the hardened architecture in `03_DATABASE_SCHEMA_BIBLE.md` and `CIVIX_SCHEMA_HARDENING_REPORT.md` is internally consistent. Identify any remaining contradictions before DDL begins.

**Prerequisites**: Phase 0 complete

**Deliverables**:
- [ ] Cross-reference check: every entity in `04_DATA_MODEL_AND_ONTOLOGY.md` appears in `03_DATABASE_SCHEMA_BIBLE.md`
- [ ] Cross-reference check: every predicate in `predicate_enum` is used in at least one adversarial test
- [ ] Cross-reference check: ADRs in `CIVIX_CHANGE_CONTROL.md` are reflected in Bibles
- [ ] `database/schema_postgres.sql` annotated as SUPERSEDED (not deleted — kept for reference)
- [ ] `database/schema_neo4j.cypher` annotated as SUPERSEDED

**Tests**: Manual cross-reference verification by a new agent reading docs cold.

**Exit gate**: Zero contradictions found between Bibles. All ADRs reflected.

**Risks**: An agent reading docs finds a gap not caught in Phase 0. Record it in `21_KNOWN_GAPS_AND_RISKS.md` and update the relevant Bible before proceeding.

---

## Phase 2 — PostgreSQL Logical Model (No DDL Yet)

**Objective**: Convert the schema Bible into a formal entity-relationship diagram and a complete logical model (tables + columns + constraints, in text form). This is the last opportunity to catch modeling errors before SQL is written.

**Prerequisites**: Phase 1 complete

**Deliverables**:
- [ ] `docs/CIVIX_ERD.md` — Entity-relationship diagram (Mermaid or similar)
- [ ] Updated `03_DATABASE_SCHEMA_BIBLE.md` with any corrections found during ERD work

**Exit gate**: ERD validates against all 30 adversarial tests conceptually.

---

## Phase 3 — PostgreSQL Physical Schema (DDL Begins)

**Objective**: Write the 18 SQL migration files. No tables may be created that are not in `03_DATABASE_SCHEMA_BIBLE.md`.

**Prerequisites**: Phase 2 complete

**Files to create** (in exact order):

```
database/migrations/
├── 01_extensions.sql
├── 02_enums.sql
├── 03_users.sql
├── 04_source.sql
├── 05_identity.sql
├── 06_domains.sql
├── 07_telecom.sql
├── 08_finance.sql
├── 09_cases.sql
├── 10_epistemic.sql
├── 11_workflow.sql
├── 12_forensic_stub.sql
├── 13_security.sql
├── 14_provenance.sql
├── 15_synthetic.sql
├── 16_rls.sql
├── 17_triggers.sql
└── 18_indexes.sql
```

**Constraints on DDL agent**:
- Every table name must match the Bible
- Every column name must match the Bible
- No new tables may be added without a new ADR
- `database/schema_postgres.sql` must NOT be used as a source
- Every migration file must be idempotent (IF NOT EXISTS, CREATE OR REPLACE)

**Tests**:
```bash
# Apply all migrations to a fresh test database
docker run -d --name civix-test-pg postgres:16
psql -h localhost -U postgres -f database/migrations/01_extensions.sql
# ... repeat for all 18 files
pytest tests/schema/ -v  # Schema constraint tests
```

**Exit gate**:
- All 18 migrations apply cleanly to a fresh PostgreSQL 16 instance
- All schema constraint tests pass (see `18_TESTING_VALIDATION_BIBLE.md` Section 5)
- Rollback works: drop all civix schema and re-apply migrations successfully

**Rollback strategy**: Drop `civix` schema: `DROP SCHEMA civix CASCADE`. Re-apply migrations.

---

## Phase 4 — Migration Framework Setup

**Objective**: Establish a proper database migration management tool.

**Prerequisites**: Phase 3 DDL files created

**Decision required**: Alembic vs Flyway vs Liquibase vs custom
STATUS: OPEN DECISION

**Deliverables**:
- [ ] Migration tool configured
- [ ] Migrations converted to tool format
- [ ] Up/down migrations verified

---

## Phase 5 — Synthetic Data Ingestion

**Objective**: Ingest the Golden World synthetic dataset (output/ CSV and JSON files) into PostgreSQL.

**Prerequisites**: Phase 3 complete, Phase 4 complete

**Files to ingest** (from `output/`):
- `cdrs.csv` (385 rows) → source_record → observation → event → event_participant → assertion
- `transactions.csv` (50 rows) → same pipeline
- `vehicle_sightings.csv` (8 rows) → same pipeline
- `surveillance_reports.json` (12 reports) → same pipeline
- `intelligence_reports.json` (5 reports) → same pipeline, with confidential informant handling
- `criminal_history_records.csv` (6 rows) → case_entity_role
- `property_transfers.csv` (3 rows) → event(PROPERTY_MUTATION) + event_participant × N

**Critical ingestion rules** (from `12_SYNTHETIC_DATA_BIBLE.md`):
- `Person.is_criminal = True` → `case_entity_role(SUSPECT)` for relevant cases
- `UNKNOWN-IMEI` → `source_identity(IMEI)`, not `device`
- `"Network Beta)"` in transactions → `source_identity(OTHER)`, not `financial_account`
- All rows tagged with `generation_run_id`
- H4: property_transfers.csv has 3 rows but canonical H4 is ONE event affecting TWO properties — create the correct single `event(PROPERTY_MUTATION)` with two `event_participant(TARGET_PROPERTY)` rows

**Tests**:
```python
# Golden World regression
assert count(SELECT entity_id FROM civix.person WHERE gen_run = $run) == 55
assert count(SELECT entity_id FROM civix.network ...) == 3
# ... for all 15 cardinalities
# Verify Amit P-02 ↔ Harish P-09 shared account assertion exists
# Verify Rekha Verma lead is FALSE_POSITIVE
```

**Exit gate**: All 30 adversarial tests from `18_TESTING_VALIDATION_BIBLE.md` pass against ingested data.

---

## Phase 6 — Forensic/Medical Stub Ingestion

**Objective**: Demonstrate forensic and medical evidence ingestion using MVP stub tables.

**Prerequisites**: Phase 5 complete

**Note**: No actual forensic/medical data in Golden World v2.1. Phase 6 creates sample synthetic forensic records for demo purposes.

**STATUS**: DEFERRED (Optional Demo Data) — Does NOT block Phase 7

---

## Phase 7 — Neo4j Projection

**Objective**: Set up the outbox → CDC consumer → Neo4j pipeline and project the Golden World data.

**Prerequisites**: Phase 5 complete

**Deliverables**:
- [ ] CDC consumer implementation (language/framework: OPEN DECISION)
- [ ] Idempotent Cypher upserts for all node types
- [ ] Tombstone handling for expunged records
- [ ] Graph constraints and indexes from schema_neo4j.cypher (rewritten to match architecture)
- [ ] Verify: `MATCH (n:Person) RETURN count(n)` = 55

**Tests**:
- Neo4j node counts match PostgreSQL entity counts
- Relationship types match event_participant roles
- CONTRADICT stance NOT projected as topological edge
- Expungement test: expunge one entity in PostgreSQL, verify Neo4j DETACH DELETE

---

## Phase 8 — Backend / API

**Objective**: Implement the backend API.

**Prerequisites**: Phase 7 complete, API framework decided

**Deliverables** (see `15_API_BACKEND_BIBLE.md`):
- [ ] Authentication middleware
- [ ] Session management (SET LOCAL civix.current_user_id)
- [ ] All required endpoints (minimum 15 from `15_API_BACKEND_BIBLE.md`)
- [ ] RLS enforcement verified

**Status**: PARTIALLY COMPLETE (Missing major endpoints required by 15_API_BACKEND_BIBLE.md). Architectural blockers (ADR-026 through ADR-029) are formally resolved.
> **Blocker**: A schema migration for ADR-026 (adding `target_entity_id` and `hypothesis_id` to `civix.investigative_lead`) MUST be created and applied before API implementation can resume.
---

## Phase 9 — Authentication, RBAC & Audit

**Objective**: Complete security hardening.

**Prerequisites**: Phase 8 complete

**Deliverables**:
- [ ] External auth provider integration
- [ ] JWT validation middleware
- [ ] Case access management API
- [ ] Audit log API
- [ ] Expungement workflow API
- [ ] Legal restriction management

**Status**: PARTIALLY COMPLETE (Missing audit and expungement APIs).

---

## Phase 10 — ML Feature Generation

**Objective**: Extract ML features from Neo4j and PostgreSQL for the Golden World scenario.

**Prerequisites**: Phase 7 complete

**Deliverables**:
- [ ] Feature extraction pipeline (AS-OF queries, generation_run_id filter)
- [ ] Graph-based features (PageRank, Louvain community detection)
- [ ] Anomaly detection models (communication burst, financial spike)
- [ ] Identity candidate generation (similarity model)

**Status**: Requirements satisfied by the expedited out-of-sequence execution of historical Phase 7 Task 3.

---

## Phase 11 — Synthetic Scale Expansion

**Objective**: Generate large-scale synthetic datasets for ML training.

**Prerequisites**: Phase 10 complete

STATUS: OPEN DECISION — Synthetic World Factory architecture.

---

## Phase 12 — Validation & Adversarial Testing

**Objective**: Run all 30 adversarial tests as automated integration tests.

**Prerequisites**: Phase 7 complete (Decoupled from Phase 8 for database/graph-level adversarial validation)

**Deliverables**:
- [ ] Full test suite for all 30 adversarial scenarios
- [ ] Performance benchmarks against targets in `18_TESTING_VALIDATION_BIBLE.md`
- [ ] Security penetration tests (RLS bypass attempts)
- [ ] False positive rate for FL-06 = 0%

---

## Phase 13 — End-to-End Integration

**Objective**: Full pipeline from ingestion to Neo4j to API to frontend.

**Prerequisites**: Phases 8–12 complete

---

## Phase 14 — Demo Readiness

**Objective**: SIH 2026 demo-ready state.

**Prerequisites**: Phase 13 complete

**Demo scenario**: Investigator logs in → opens CIVIX case → sees entity graph → discovers hidden connection between Amit and Harish → creates hypothesis → system suggests leads → investigator disposes leads → falsifies Rekha Verma lead.

---

## Important: No Phase May Skip Its Prerequisites

If a phase cannot start because of an OPEN DECISION, record the blocker in `21_KNOWN_GAPS_AND_RISKS.md` and escalate for decision. Do not work around it silently.
