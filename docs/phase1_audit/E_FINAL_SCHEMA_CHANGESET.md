# E — FINAL SCHEMA CHANGESET
## CIVIX Phase 1 — Conceptual Changes Required Before DDL

**Date**: 2026-08-29 | **Status**: FINAL — Awaiting Human Authorization

> [!IMPORTANT]
> This document does NOT contain SQL.
> It describes the exact conceptual changes required to `03_DATABASE_SCHEMA_BIBLE.md` before Migration DDL begins.
> Every change is mapped to a Blocker ID and reason.
> Changes requiring new ADRs are flagged.

---

## Change Priority Legend

| Priority | Meaning |
|---|---|
| P0 — CRITICAL | Must be done before Migration 02 (ENUM definitions) can be written |
| P1 — HIGH | Must be done before Migration 10 (epistemic pipeline) |
| P2 — MEDIUM | Must be done before Phase 3 finalization |
| P3 — LOW | Can be done in a follow-up revision |

---

## P0 — CRITICAL: Must Resolve Before Any DDL

### CHANGE-01: Define Five Missing ENUM Types
**Blocker**: BLK-01  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 02 (ENUM Types)  
**Change Type**: ADD CONTROLLED VOCABULARY  

Add to Migration 02:

```
hypothesis_status_enum: ACTIVE, UNDER_REVIEW, CONFIRMED, REFUTED, ARCHIVED
  - ACTIVE: being evaluated
  - UNDER_REVIEW: escalated for supervisor review
  - CONFIRMED: human-authorized conclusion
  - REFUTED: human-authorized rejection
  - ARCHIVED: no longer actively evaluated

lead_priority_enum: CRITICAL, HIGH, MEDIUM, LOW (mirrors case_priority_enum)

lead_status_enum: OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED
  - OPEN: awaiting assignment
  - IN_PROGRESS: under investigation
  - CONFIRMED: lead was valid
  - FALSE_POSITIVE: lead was invalid (FL-06 case)
  - CLOSED: administratively closed
  - DEFERRED: postponed

task_type_enum: INTERVIEW, SURVEILLANCE, SEARCH_AND_SEIZURE, FORENSIC_COLLECTION,
                FINANCIAL_REVIEW, LEGAL_REQUEST, COURT_ORDER, DATA_ANALYSIS,
                FIELD_VERIFICATION, OTHER

task_status_enum: PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED
```

**New ADR**: Requires user confirmation of hypothesis_status values (especially REFUTED vs ARCHIVED semantics).

---

### CHANGE-02: Define Source Agency Type ENUM
**Blocker**: BLK-15 (partial)  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 02  
**Change Type**: ADD CONTROLLED VOCABULARY  

```
source_agency_type_enum: TELECOM, BANK, POLICE, COURT, REVENUE_OFFICE, INFORMANT,
                         CCTV_SYSTEM, HOSPITAL, FORENSIC_LAB, OSINT, OTHER
```

Change `civix.source.agency_type TEXT NOT NULL` → `agency_type source_agency_type_enum NOT NULL`

---

### CHANGE-03: Remove `extraction_id` from `source_identity`
**Blocker**: BLK-03  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 05  
**Change Type**: REMOVE ATTRIBUTE  
**New ADR Required**: ADR-019

Remove: `extraction_id UUID NULL FK→extraction` from `civix.source_identity`

Document replacement: When a source_identity is created by AI extraction, create a `civix.provenance` record:
- `derived_type = 'SOURCE_IDENTITY'`
- `derived_id = new source_identity entity_id`
- `source_type = 'EXTRACTION'`
- `source_id = extraction_id`
- `derivation_method = 'AI_NER'` (or appropriate type)

**Reason**: Contradicts ADR-006. Provenance table is the correct cross-entity linkage mechanism.

---

### CHANGE-04: Fix Neo4j Relationship Type Design
**Blocker**: BLK-04  
**Target File**: `13_NEO4J_GRAPH_BIBLE.md`  
**Change Type**: CHANGE RELATIONSHIP MODEL  
**New ADR Required**: ADR-013

Replace two separate relationship types:
- `[:SUPPORTS]` Assertion → Hypothesis
- `[:CONTRADICTS]` Assertion → Hypothesis

With a single relationship type:
```
[:HAS_STANCE {
  stance: 'SUPPORT' | 'CONTRADICT' | 'NEUTRAL' | 'INCONCLUSIVE',
  weight: float,
  assigned_by: uuid (optional),
  tx_start: datetime
}]
```

Graph algorithm queries must filter:
```cypher
WHERE r.stance = 'SUPPORT'
```

**Reason**: A named relationship type in Neo4j IS a structural graph edge. Having a `[:CONTRADICTS]` type that is "not structural" is a logical impossibility. This creates an unimplementable specification.

---

### CHANGE-05: Resolve LOC-* Location Coordinate Strategy
**Blocker**: BLK-05  
**Target File**: `12_SYNTHETIC_DATA_BIBLE.md`, `08_SPATIOTEMPORAL_MODEL.md`  
**Change Type**: ADD ENTITY DEFINITIONS  

**Decision required from user**. Recommended option:

Create `docs/location_master.json` — a mapping of LOC-01 through LOC-30 to:
```json
{
  "LOC-01": {
    "name": "Ajmer City Centre Area",
    "location_type": "ESTIMATED_POINT",
    "lat": 26.4499,
    "lon": 74.6399,
    "uncertainty_radius_meters": 3000
  },
  ...
}
```

This file is NOT a frozen world artifact — it is ingestion configuration. It defines the physical meaning of world location IDs.

**Reason**: Without coordinates, `civix.location` rows for LOC-* cannot be created during Phase 5 ingestion.

---

## P1 — HIGH: Must Resolve Before Epistemic/Workflow DDL

### CHANGE-06: Add Bitemporal Fields to `hypothesis_support`
**Blocker**: BLK-06  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 10  
**Change Type**: ADD ATTRIBUTE, CHANGE CONSTRAINT  
**New ADR Required**: ADR-012

Add to `civix.hypothesis_support`:
- `tx_start TIMESTAMPTZ NOT NULL DEFAULT now()`
- `tx_end TIMESTAMPTZ NULL`

Change:
- `UNIQUE(hypothesis_id, assertion_id)` → `UNIQUE(hypothesis_id, assertion_id) WHERE tx_end IS NULL`

Add application rule:
- Stance change = set `tx_end = now()` on old row, insert new row with new stance

**Reason**: Stance assessments are investigative decisions and must have an immutable audit trail. The current schema allows silent mutation with no history.

---

### CHANGE-07: Add `analysis_run.status` Field
**Blocker**: ADV-22 (FAIL scenario)  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 10  
**Change Type**: ADD ATTRIBUTE  

Add to `civix.analysis_run`:
- `status TEXT NOT NULL DEFAULT 'COMPLETED'` (ENUM: RUNNING, COMPLETED, FAILED, VOIDED)
- `voided_at TIMESTAMPTZ NULL`
- `voided_by UUID FK→civix_user NULL`
- `void_reason TEXT NULL`

Add application rule: When an analysis_run is voided, all `extraction.is_superseded = TRUE` for extractions from that run. All assertions from that run should have `epistemic_status = REFUTED`.

**Reason**: There is no mechanism to invalidate a faulty ML analysis run. Without this, corrupted AI-generated assertions cannot be systematically revoked.

---

### CHANGE-08: Add `observer_entity_id` to `observation`
**Blocker**: BLK-13  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 10  
**Change Type**: ADD ATTRIBUTE  
**New ADR Required**: ADR-015

Add to `civix.observation`:
- `observer_entity_id UUID FK→entity NULL`

Rules:
- CIVIX system users who are also investigative persons: populate BOTH `observed_by` and `observer_entity_id`
- Field officers who are not CIVIX system users: populate only `observer_entity_id`
- Automated sensors (CCTV, signal): populate neither (use `observer_type` ENUM to indicate)

**Reason**: Surveillance reports reference `"observing_officer": "Constable Vijay Kumar (P-28)"`. P-28 is a Person in the world who may not have a CIVIX system account.

---

### CHANGE-09: Add `classification_level` to `evidence_artifact`
**Blocker**: BLK-12  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 04  
**Change Type**: ADD ATTRIBUTE  

Add to `civix.evidence_artifact`:
- `classification_level clearance_enum NOT NULL DEFAULT 'UNCLASSIFIED'`

Application rule: Intelligence reports classified as "Secret" produce evidence_artifact rows with `classification_level = SECRET`. Users with clearance < SECRET cannot access those artifacts (clearance enforcement — open decision on mechanism).

**Reason**: Intelligence reports have `classification: "Secret"` field. There is currently no field in the schema to capture evidence classification level.

---

### CHANGE-10: Fix `case_access` UNIQUE Constraint
**Blocker**: BLK-08  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 09  
**Change Type**: CHANGE CONSTRAINT  

Remove: `UNIQUE(case_id, user_id)` from `civix.case_access`

Replace with: (expressed as description, not SQL)
A partial unique constraint on active (non-revoked) records only:
- Only ONE active access record per (case_id, user_id) pair at any time
- Historical records (where `is_revoked = TRUE`) are not subject to the uniqueness restriction

**Reason**: Changing a user's permission level (READ → WRITE → ADMIN) requires revoking the old record and creating a new one. The table's own `is_revoked` column implies this pattern, but the UNIQUE constraint prevents it.

---

### CHANGE-11: Add Assertion Cross-Case Access Control
**Blocker**: ADV-19 (FAIL scenario)  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 10, `10_SECURITY_RBAC_AUDIT_BIBLE.md`  
**Change Type**: ADD SECURITY RULE  

**Option A (Recommended for MVP)**: Add `case_id UUID FK→investigative_case NULL` to `civix.assertion`.

Rules:
- Assertions created from case-specific evidence carry the case_id
- Cross-case shared assertions (authorized via case_link) can have NULL case_id
- RLS: user can read assertion WHERE case_id IS NULL OR case_id IN (user's authorized cases)

**Option B**: Leave assertion case-agnostic; enforce access at the hypothesis_support level (user can only create hypothesis_support for their authorized case's hypotheses).

**Decision required from user**: Option A adds a case_id FK to assertion (significant change). Option B accepts the current design with a documented limitation.

**New ADR Required**: ADR-016 (or MODIFY assertion column)

---

### CHANGE-12: Resolve `civix_user` Multi-Role Decision
**Blocker**: BLK-09  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 03, `10_SECURITY_RBAC_AUDIT_BIBLE.md`  
**Change Type**: ARCHITECTURE DECISION  
**New ADR Required**: ADR-018  

**Decision required from user**.

Recommended (MVP Option A): Accept single global role on `civix_user`. Document that:
- `civix_user.role` = maximum capability level globally
- `case_access.permission_level` = specific case permission (may be lower than global role)
- No multi-role assignment in Phase 1

This is the simplest design and sufficient for SIH demo.

---

### CHANGE-13: Expungement Free-Text PII Decision
**Blocker**: BLK-10  
**Target File**: `10_SECURITY_RBAC_AUDIT_BIBLE.md`, `03_DATABASE_SCHEMA_BIBLE.md`  
**Change Type**: ADD SECURITY RULE  
**New ADR Required**: ADR-017  

**Decision required from user**.

Recommended (Option B — Accepted Risk for MVP): Accept that free-text fields (`lead_text`, `observation_text`, `hypothesis_text`, `assertion.object_value`) may contain PII of expunged entities. RLS restricts access to the entity record itself. Free-text redaction is deferred to Phase 9 (legal compliance hardening).

Document this as a known risk in `21_KNOWN_GAPS_AND_RISKS.md`.

---

## P2 — MEDIUM: Before Phase 3 Finalization

### CHANGE-14: Define Eight Missing ENUM Types (TEXT Fields)
**Blocker**: BLK-15  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 02  
**Change Type**: ADD CONTROLLED VOCABULARY × 8  

For each field, convert from TEXT to proper ENUM:

| Field | Table | ENUM Name | Values |
|---|---|---|---|
| `observer_type` | observation | `observer_type_enum` | HUMAN_OFFICER, SENSOR_CCTV, SENSOR_SIGNAL, AI_EXTRACTION, AUTOMATED_SYSTEM, INFORMANT, UNKNOWN |
| `observation_type` | observation | `observation_type_enum` | PHYSICAL_SURVEILLANCE, CDR_OBSERVATION, FINANCIAL_OBSERVATION, VEHICLE_SIGHTING, FORENSIC_OBSERVATION, DOCUMENT_OBSERVATION, INTELLIGENCE_REPORT, DIGITAL_FORENSICS, OTHER |
| `holder_role` | account_holder | `account_holder_role_enum` | PRIMARY, JOINT, AUTHORIZED_SIGNATORY, POA, NOMINEE, CORPORATE_DIRECTOR |
| `gender` | person | `gender_enum` | MALE, FEMALE, OTHER, UNDISCLOSED |
| `severity` | data_quality_issue | `issue_severity_enum` | CRITICAL, HIGH, MEDIUM, LOW, INFO |
| `scope` | legal_restriction | `restriction_scope_enum` | FULL_RECORD, IDENTITY_ONLY, CONTENT_ONLY, ANALYTICAL_ONLY |
| `status` | legal_restriction | `restriction_status_enum` | ACTIVE, LIFTED, EXPIRED |
| `legal_status` | evidence_instance | `evidence_legal_status_enum` | ACTIVE, RESTRICTED, SEALED, EXPUNGED |
| `device_type` | device | `device_type_enum` | MOBILE_PHONE, SIM_DEVICE, LAPTOP, TABLET, ROUTER, VEHICLE_GPS, OTHER |
| `property_type` | property | `property_type_enum` | AGRICULTURAL_LAND, RESIDENTIAL, COMMERCIAL, INDUSTRIAL, PLOT, OTHER |
| `number_type` | phone_number | `phone_number_type_enum` | MOBILE_PREPAID, MOBILE_POSTPAID, LANDLINE, VOIP, OTHER |

---

### CHANGE-15: Remove Redundant `assertion.object_location_id`
**Blocker**: BLK-17  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 10  
**Change Type**: REMOVE ATTRIBUTE  

Remove: `object_location_id UUID FK→location NULL` from `civix.assertion`

Update CHECK constraint:
- From: `CHECK (object_entity_id IS NOT NULL OR object_value IS NOT NULL OR object_location_id IS NOT NULL)`
- To: `CHECK (object_entity_id IS NOT NULL OR object_value IS NOT NULL)`

Spatial assertions use `object_entity_id FK→entity` where the entity is a `civix.location` subtype.

**Reason**: `location` is already a subtype of `entity`. The `object_location_id` column creates a redundant second path to the same location entity, creating inconsistency risk.

---

### CHANGE-16: Add `tx_start/tx_end` to `case_entity_role`
**Blocker**: BLK-18  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 09  
**Change Type**: ADD ATTRIBUTE, CHANGE TEMPORAL RULE  

Add to `civix.case_entity_role`:
- `tx_start TIMESTAMPTZ NOT NULL DEFAULT now()`
- `tx_end TIMESTAMPTZ NULL`

Change existing:
- `valid_from DATE NULL` → `valid_from TIMESTAMPTZ NULL`
- `valid_to DATE NULL` → `valid_to TIMESTAMPTZ NULL`

**Reason**: Criminal role transitions can happen intra-day. DATE granularity is insufficient for precise temporal tracking of case role changes.

---

### CHANGE-17: Add Provenance Indexes to Migration 18
**Blocker**: BLK-16  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 18 (indexes)  
**Change Type**: ADD INDEX  

Add to Migration 18:
```
INDEX: civix.provenance(derived_id, derived_type) — required for forward provenance traversal
INDEX: civix.provenance(source_id, source_type) — required for reverse provenance traversal
INDEX: civix.assertion(subject_entity_id) — high-frequency query path
INDEX: civix.assertion(object_entity_id) — high-frequency query path
INDEX: civix.hypothesis_support(hypothesis_id, assertion_id) — unique check + lookup
INDEX: civix.event_participant(event_id) — N-ary participant lookup
INDEX: civix.event_participant(entity_id) — entity's event history
INDEX: civix.case_entity_role(case_id, entity_id) — case entity lookup
INDEX: civix.audit_event(user_id, timestamp DESC) — user activity audit
INDEX: civix.audit_event(target_id) — specific resource audit trail
```

---

### CHANGE-18: Add `fir.status` Field
**Blocker**: FINDING-34  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` — Migration 09  
**Change Type**: ADD ATTRIBUTE  

Add to `civix.fir`:
- `fir_status TEXT NOT NULL DEFAULT 'OPEN'`  (future: convert to `fir_status_enum`)
- Values: OPEN, CHARGE_SHEETED, CLOSED_BY_COURT, ABATED, TRANSFERRED

`criminal_history_records.csv` has `status: "Fine Paid", "Acquitted"` — these map to `case_entity_role` disposition, not FIR status. But the FIR itself needs a lifecycle status field.

---

### CHANGE-19: Fix `test_world.py` Hard-coded Path
**Blocker**: BLK-20  
**Target File**: `civix_generator/tests/test_world.py`  
**Change Type**: CODE FIX (not a Bible change)  
**Human Authorization Required**: NO  

This is a code-level fix, not a schema change. The path should be environment-driven:
```python
import os
path = os.environ.get("CIVIX_SYNTHETIC_WORLD_PATH", 
    os.path.join(os.path.dirname(__file__), "../../docs/synthetic_world.md"))
```

---

### CHANGE-20: Fix Validator Default Values in `validators.py`
**Blocker**: BLK-14  
**Target File**: `civix_generator/world/validators.py`  
**Change Type**: CODE FIX (not a Bible change)  
**Human Authorization Required**: NO  

Import `EXPECTED_COUNTS` from `config.py` and use it instead of hard-coded defaults (18 for vehicles, 24 for accounts).

---

## P3 — LOW: Follow-up Revisions

### CHANGE-21: Fix ADR-021 Dangling Reference
**Blocker**: BLK-19  
**Target File**: `03_DATABASE_SCHEMA_BIBLE.md` line 444  
**Change Type**: DOCUMENTATION FIX  

Change: `(ADR-021, see 05_EPISTEMIC_MODEL.md)` → `(see 05_EPISTEMIC_MODEL.md)`

Until the no-entity-FKs-on-event decision receives a formal ADR number.

---

### CHANGE-22: Document ingestion ordering for property transfers
**Blocker**: ADV-27  
**Target File**: `12_SYNTHETIC_DATA_BIBLE.md`  
**Change Type**: ADD DOCUMENTATION  

Add an explicit ingestion ordering section:
1. Create location entities (LOC-*) first
2. Create person entities (P-*)
3. Create vehicle/account/property entities
4. Create source and source_record rows
5. Create evidence_artifact and evidence_instance rows
6. Create event and event_participant rows
7. Create observation and extraction rows
8. Create source_identity rows (and provenance links)
9. Create assertion rows (and provenance links)

---

## Required ADR Summary

| ADR # | Topic | Priority |
|---|---|---|
| ADR-012 | hypothesis_support bitemporal versioning | HIGH |
| ADR-013 | Neo4j HAS_STANCE relationship type | HIGH |
| ADR-015 | observer_entity_id vs observed_by | MEDIUM |
| ADR-016 | assertion.case_id OR enforcement at hypothesis_support | HIGH |
| ADR-017 | Expungement free-text PII handling | HIGH |
| ADR-018 | civix_user single-role decision | HIGH |
| ADR-019 | Remove extraction_id from source_identity | HIGH |

---

## Count of Changes Required

| Priority | Count | Count Requiring Human Auth |
|---|---|---|
| P0 — CRITICAL | 5 | 5 |
| P1 — HIGH | 8 | 6 |
| P2 — MEDIUM | 9 | 3 |
| P3 — LOW | 3 | 0 |
| **TOTAL** | **25** | **14** |
