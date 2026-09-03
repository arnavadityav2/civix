# Phase 6: Pre-Migration Architecture Decision Log

**Date**: 2026-08-30
**Status**: APPROVED

This document records the architectural corrections made to the database schema prior to generating Alembic migrations, resolving ambiguities found in the initial Phase 6 audit.

---

## 1. GiST Temporal Exclusion (`btree_gist`)

- **Decision**: Explicitly require the `btree_gist` PostgreSQL extension in `001_extensions.py` to enable scalar `UUID` equality inside GiST exclusion constraints (`sim_number_assignment`).

---

## 2. UUID Strategy

- **Decision**: Target PostgreSQL 16. Standardize 100% on native `gen_random_uuid()`. `uuid-ossp` is rejected.

---

## 3. Entity Subtype Integrity

- **Decision**: Discriminator-based composite Foreign Key approach. `civix.entity` adds `UNIQUE (entity_id, entity_type)`. Subtypes define their FK as `FOREIGN KEY (entity_id, entity_type) REFERENCES entity (entity_id, entity_type)` along with a `CHECK (entity_type = '...')` constraint.

---

## 4. Row-Level Security (RLS) Architecture

- **Decision**: Secure, session-variable driven RLS joining against `case_access`.
- **Database Enforcement**:
  1. Alembic migrations will NOT embed plain-text passwords (`WITH LOGIN PASSWORD '...'`) to prevent secrets in Git. Role provisioning is delegated to deployment automation.
  2. The application role must be a non-superuser, non-owner role, explicitly lacking the `BYPASSRLS` attribute.
  3. Transactions must be scoped via `SET LOCAL civix.current_user_id = 'uuid'` to prevent identity bleed across connection pools.
  4. Policies will use `current_setting('civix.current_user_id', true)` so missing settings securely fail closed (return NULL) rather than raising exceptions.
  5. `FOR ALL USING (...) WITH CHECK (...)` will be explicitly defined to mirror access conditions.
  6. All RLS-governed tables will declare `FORCE ROW LEVEL SECURITY`.
- **RLS Matrix Enforcement**: Every case-scoped table must have an explicitly defined path to `case_id`. For example, `hypothesis_support` joins through `hypothesis`, while `medical_report` joins through `evidence_instance`. Global realities (`person`, `entity`) are globally readable (subject to `legal_restriction`), but evidence *about* them is strictly case-scoped.

---

## 5. Synthetic Data Metadata vs Ground Truth

- **Decision**: Strict structural isolation.
  - `dataset` = dataset-level metadata.
  - `scenario` = scenario/generation configuration metadata.
  - `generation_run` = execution/provenance metadata.
  - NONE of these tables stores per-entity synthetic ground-truth labels (e.g., `is_criminal`, `fraudulent_buyer_id`). Ground truth remains completely isolated in the synthetic dataset artifact layer and is banned from the operational schema.

---

## 6. Deletion, Redaction, and Legal Retention

- **Decision**: Categorized mutability definitions enforced by database triggers, not application convention.
  1. **Immutable / Audit Tables**: `audit_event`, `source_record`, `evidence_artifact`, `identity_merge_event`, `identity_resolution`, `identity_split_event`, `legal_restriction`, and `provenance`. A `BEFORE UPDATE OR DELETE` trigger hard-blocks all mutations regardless of `generation_run_id`.
  2. **System/Lifecycle Tables**: Explicitly defined retention/deletion semantics. For example, `outbox` records are designed to be consumed and deleted by CDC workers.
  3. **Synthetic-Deletable Operational Tables**: Any operational table not classified above (e.g., `person`, `hypothesis`, `device`) receives a `BEFORE DELETE` trigger. This trigger throws an exception if `generation_run_id IS NULL`. Operational deletion of non-synthetic data is impossible.
  4. **Restrictable**: Managed via `legal_restriction` table. RLS policies explicitly exclude records where `restriction_type IN ('EXPUNGED', 'SEALED')`.
