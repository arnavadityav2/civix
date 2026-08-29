# 14 — PostgreSQL Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: Ready for DDL implementation

---

## 1. PostgreSQL Version & Extensions

**Minimum version**: PostgreSQL 16

Required extensions:
```sql
CREATE EXTENSION IF NOT EXISTS postgis;        -- Spatial geometry
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";    -- UUID generation (legacy compatibility)
CREATE EXTENSION IF NOT EXISTS pgcrypto;       -- gen_random_uuid() (preferred)
CREATE EXTENSION IF NOT EXISTS btree_gist;     -- GIST indexes on scalar types (temporal exclusion)
```

---

## 2. Schema Strategy

All tables reside in the `civix` schema:
```sql
CREATE SCHEMA IF NOT EXISTS civix;
SET search_path TO civix, public;
```

The `public` schema is reserved for extensions (PostGIS functions, etc.).

---

## 3. DDL Migration Order

| File | Contents | Prerequisites |
|---|---|---|
| `01_extensions.sql` | Extensions | None |
| `02_enums.sql` | All ENUM types | Extensions |
| `03_users.sql` | `civix_user` | Enums |
| `04_source.sql` | `source`, `source_record`, `evidence_artifact`, `evidence_instance` | Users |
| `05_identity.sql` | `entity`, `source_identity`, `person`, `person_alias`, `identity_candidate`, `identity_resolution`, `identity_merge_event`, `identity_split_event` | Source |
| `06_domains.sql` | `phone_number`, `sim`, `device`, `vehicle`, `property`, `financial_account`, `organization`, `network`, `location` | Identity |
| `07_telecom.sql` | `sim_number_assignment`, `sim_in_device` | Domains |
| `08_finance.sql` | `account_holder` | Domains |
| `09_cases.sql` | `investigative_case`, `fir`, `case_entity_role`, `case_access`, `case_link` | Users, Identity |
| `10_epistemic.sql` | `analysis_run`, `observation`, `extraction`, `event`, `event_participant`, `assertion`, `hypothesis`, `hypothesis_support` | Source, Identity, Cases |
| `11_workflow.sql` | `investigative_lead`, `investigation_task` | Cases, Epistemic |
| `12_forensic_stub.sql` | `forensic_report`, `medical_report` (MVP stubs) | Source |
| `13_security.sql` | `legal_restriction`, `audit_event`, `outbox` | Users, Identity, Cases |
| `14_provenance.sql` | `provenance`, `data_quality_issue` | All above |
| `15_synthetic.sql` | `dataset`, `scenario`, `generation_run` | None |
| `16_rls.sql` | PostgreSQL Row Level Security policies | All tables |
| `17_triggers.sql` | Audit immutability, TOMBSTONE generation, updated_at triggers | All tables |
| `18_indexes.sql` | BRIN indexes (time columns), GiST spatial, B-tree performance | All tables |

---

## 4. Bitemporal Pattern

Most tables use a two-column transaction time:
```sql
tx_start TIMESTAMPTZ NOT NULL DEFAULT now(),
tx_end   TIMESTAMPTZ NULL  -- NULL = currently valid
```

Some use TSTZRANGE for valid time:
```sql
valid_time TSTZRANGE NOT NULL  -- real-world validity
```

AS-OF query pattern:
```sql
-- What was true at a specific moment (historical reconstruction)?
WHERE tx_start <= $as_of AND (tx_end IS NULL OR tx_end > $as_of)
```

---

## 5. Immutability Patterns

### 5.1 Append-Only Tables (audit_event)
```sql
-- Trigger prevents modifications
CREATE TRIGGER prevent_modification
BEFORE UPDATE OR DELETE ON civix.audit_event
FOR EACH ROW EXECUTE FUNCTION civix.raise_immutability_error();
```

### 5.2 Supersession Pattern (source_record, identity_resolution)
```sql
-- Correction inserts new row and sets superseded_by on old row
UPDATE civix.source_record
SET superseded_by = $new_record_id
WHERE source_record_id = $old_id;

INSERT INTO civix.source_record (...) VALUES (...);
```

---

## 6. Performance Indexes (Migration 18)

### Time-series tables (BRIN indexes — CDRs, events)
```sql
CREATE INDEX CONCURRENTLY idx_event_occurred_at
ON civix.event USING BRIN (lower(occurred_at));
```

### Spatial indexes (GiST — location)
```sql
CREATE INDEX CONCURRENTLY idx_location_geometry
ON civix.location USING GIST (geometry);
```

### ENUM + FK compound indexes
```sql
CREATE INDEX CONCURRENTLY idx_assertion_subject_predicate
ON civix.assertion (subject_entity_id, predicate);

CREATE INDEX CONCURRENTLY idx_event_participant_event_role
ON civix.event_participant (event_id, participant_role);
```

### JSON GIN indexes (JSONB fields)
```sql
CREATE INDEX CONCURRENTLY idx_observation_structured_content
ON civix.observation USING GIN (structured_content);
```

---

## 7. Partitioning Strategy (Large-Scale)

For production scale:
- `civix.event` — partition by `lower(occurred_at)` (monthly range)
- `civix.audit_event` — partition by `timestamp` (monthly range)
- `civix.assertion` — partition by `tx_start` (monthly range)

STATUS: OPEN DECISION — partitioning should be applied before data volume exceeds 10M rows per table.

---

## 8. Row Level Security

Example policies:
```sql
ALTER TABLE civix.evidence_instance ENABLE ROW LEVEL SECURITY;

CREATE POLICY evidence_case_access ON civix.evidence_instance
  USING (
    case_id IN (
      SELECT case_id FROM civix.case_access
      WHERE user_id = current_setting('civix.current_user_id')::UUID
        AND is_revoked = FALSE
        AND (valid_until IS NULL OR valid_until > now())
    )
  );
```

Application must set `civix.current_user_id` at the start of each session:
```sql
SET LOCAL civix.current_user_id = $authenticated_user_id;
```

---

## 9. What Makes the Existing schema_postgres.sql Superseded

The file `database/schema_postgres.sql` was written before the architectural reviews. It is superseded because:

| Problem | Location |
|---|---|
| `password_hash VARCHAR(255)` on users table | Line 11 — violates ADR-010 |
| No epistemic pipeline (no observation, extraction, event, assertion, hypothesis) | Entire file |
| No bitemporal fields (tx_start, tx_end, valid_time) | Entire file |
| No PostGIS / spatial model | Entire file |
| No identity resolution model (SourceIdentity, IdentityCandidate) | Entire file |
| No case_access / RLS | Entire file |
| No provenance table | Entire file |
| `entity_master` conflates all entity types into one table with `entity_type VARCHAR(50)` | Lines 70+ |

**DO NOT USE `database/schema_postgres.sql` for implementation.** Use the DDL migration files defined in `19_IMPLEMENTATION_MASTER_PLAN.md`.
