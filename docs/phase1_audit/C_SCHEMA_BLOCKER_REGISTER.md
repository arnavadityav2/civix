# C — SCHEMA BLOCKER REGISTER
## CIVIX Phase 1 — Pre-DDL Blocker Inventory

**Date**: 2026-08-29 | **Status**: FINAL

> [!IMPORTANT]
> Any blocker with status OPEN must be resolved before Phase 3 (DDL) begins.
> PROPOSED blockers have a solution defined; they require human authorization.
> RESOLVED blockers may proceed to implementation.

---

## Severity Legend

| Severity | Meaning |
|---|---|
| CRITICAL | DDL cannot be written correctly without resolution. Will produce incorrect schema. |
| HIGH | DDL can be written but will produce an incomplete or semantically wrong schema. |
| MEDIUM | DDL can be written; gap is a refinement or should be fixed before production. |
| LOW | Minor issue; fix in next revision. |

---

## Status Legend

| Status | Meaning |
|---|---|
| OPEN | No solution proposed. Decision required. |
| PROPOSED | Solution identified. Awaiting human authorization. |
| RESOLVED | Confirmed fixed in architecture document. |
| NEEDS_DECISION | Multiple valid options exist; human must choose. |

---

## CRITICAL BLOCKERS

### BLK-01
**Gap ID**: GAP-26, GAP-27, GAP-28, GAP-29, GAP-30  
**Severity**: CRITICAL  
**Status**: PROPOSED  
**Description**: Five ENUM types referenced in table definitions are never defined.
- `hypothesis_status_enum` — used in `civix.hypothesis`
- `lead_priority_enum` — used in `civix.investigative_lead`
- `lead_status_enum` — used in `civix.investigative_lead`
- `task_type_enum` — used in `civix.investigation_task`
- `task_status_enum` — used in `civix.investigation_task`

**Evidence**: `03_DATABASE_SCHEMA_BIBLE.md` lines 479, 491, 495 reference these ENUMs. Migration 02 (ENUM definitions) does NOT include them.

**Affected Bibles**: `03_DATABASE_SCHEMA_BIBLE.md`  
**Affected Entities**: hypothesis, investigative_lead, investigation_task  

**Implementation Impact**: DDL Migration 02 cannot be completed. Migration 10 (workflow) and Migration 11 (epistemic pipeline) will fail because the types don't exist.

**Proposed Resolution**:
Add to Migration 02 (ENUM definitions):
```
hypothesis_status_enum: ACTIVE, UNDER_REVIEW, CONFIRMED, REFUTED, ARCHIVED
lead_priority_enum: CRITICAL, HIGH, MEDIUM, LOW
lead_status_enum: OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED
task_type_enum: INTERVIEW, SURVEILLANCE, SEARCH_AND_SEIZURE, FORENSIC_COLLECTION,
                FINANCIAL_REVIEW, LEGAL_REQUEST, COURT_ORDER, DATA_ANALYSIS,
                FIELD_VERIFICATION, OTHER
task_status_enum: PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED
```
**Human Authorization Required**: YES — confirm hypothesis status values (especially: is REFUTED different from ARCHIVED?)

---

### BLK-02
**Gap ID**: GAP-31  
**Severity**: CRITICAL  
**Status**: NEEDS_DECISION  
**Description**: `output/ground_truth.json` is empty (contains only `{}`).

**Evidence**: File inspection confirms 2-byte file with empty JSON object.

**Affected Bibles**: `12_SYNTHETIC_DATA_BIBLE.md`, `18_TESTING_VALIDATION_BIBLE.md`, `19_IMPLEMENTATION_MASTER_PLAN.md`  
**Affected Entities**: scenario, generation_run  

**Implementation Impact**: Phase 5 ingestion validation is designed to compare against ground_truth. Phase 12 adversarial testing relies on ground truth. ML training label availability depends on ground truth.

**Options**:
- A. Run the generator to populate ground_truth.json (requires checking if generator currently produces it)
- B. Manually populate ground_truth.json with canonical signal/entity facts from synthetic_world.md
- C. Accept that ground_truth.json is intentionally empty (no canonical ground truth in this world) — this breaks all validation plans

**Human Authorization Required**: YES — must determine whether this file should have content and who is responsible for it.

---

### BLK-03
**Gap ID**: GAP-32  
**Severity**: CRITICAL  
**Status**: PROPOSED  
**Description**: `civix.source_identity` has `extraction_id UUID FK→extraction`. This creates a direct circular dependency (`source_identity → extraction → evidence_instance → observation → (provenance) → source_identity`) and contradicts ADR-006.

**Evidence**: `03_DATABASE_SCHEMA_BIBLE.md` line 220: `| extraction_id | UUID | NULL | FK → extraction |`

**Affected Bibles**: `03_DATABASE_SCHEMA_BIBLE.md`, `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md`  
**Affected Entities**: source_identity, extraction, provenance  

**Implementation Impact**: If implemented as written, it creates a confusing and architecturally inconsistent provenance path. The provenance table exists for exactly this kind of derived-object linking.

**Proposed Resolution**: Remove `extraction_id` from `source_identity`. Instead, when a source_identity is created by an AI extraction, create a provenance record: `provenance(derived_type='SOURCE_IDENTITY', derived_id=new_si_id, source_type='EXTRACTION', source_id=extraction_id, derivation_method='AI_NER')`.

This requires **ADR-019** to be written.

**Human Authorization Required**: YES — schema change.

---

### BLK-04
**Gap ID**: GAP-38  
**Severity**: CRITICAL  
**Status**: PROPOSED  
**Description**: `13_NEO4J_GRAPH_BIBLE.md` defines `[:CONTRADICTS]` as a named Neo4j relationship type while simultaneously stating it is "never a structural edge." This is a logical impossibility — Neo4j named relationship types ARE structural edges.

**Evidence**: `13_NEO4J_GRAPH_BIBLE.md` line 69: `| [:CONTRADICTS] | ...| ⚠️ Property-based ONLY — never structural edge |`

**Affected Bibles**: `13_NEO4J_GRAPH_BIBLE.md`, `11_AI_ML_BIBLE.md`  
**Implementation Impact**: CDC consumer cannot be implemented correctly. Developer will either create two relationship types (causing algorithm contamination) or one (losing semantic distinction).

**Proposed Resolution**: Requires **ADR-013**.
Replace:
```
[:SUPPORTS] and [:CONTRADICTS] relationship types
```
With:
```
[:HAS_STANCE {stance: 'SUPPORT'|'CONTRADICT'|'NEUTRAL'|'INCONCLUSIVE', weight: float}]
```
Graph algorithm queries filter: `WHERE r.stance = 'SUPPORT'`.

**Human Authorization Required**: YES — Neo4j schema change.

---

### BLK-05
**Gap ID**: GAP-60  
**Severity**: CRITICAL  
**Status**: NEEDS_DECISION  
**Description**: Surveillance reports reference `location_id: LOC-13`, `LOC-17`, etc. The canonical world contains no coordinates for these locations. During database ingestion, these must become PostGIS geometry entries in `civix.location`. The actual coordinates are undefined.

**Evidence**: `output/surveillance_reports.json` — all 12 reports reference LOC-* IDs. The canonical world does not define coordinates for LOC-01 through LOC-30.

**Affected Bibles**: `08_SPATIOTEMPORAL_MODEL.md`, `03_DATABASE_SCHEMA_BIBLE.md`  
**Affected Entities**: location  

**Options**:
- A. Create a lookup table of LOC-* → coordinates in synthetic_world.md (frozen world modification)
- B. Create a separate `location_master.json` file with coordinates for all LOC-* IDs
- C. During ingestion, create all LOC-* as `ESTIMATED_POINT` at a default Ajmer, Rajasthan coordinate with uncertainty_radius_meters = 5000
- D. Create LOC-* as `ADMIN_BOUNDARY` polygons (city/town level)

**Human Authorization Required**: YES — affects frozen world definition and ingestion plan.

---

## HIGH BLOCKERS

### BLK-06
**Gap ID**: GAP-33  
**Severity**: HIGH  
**Status**: PROPOSED  
**Description**: `hypothesis_support` has `UNIQUE(hypothesis_id, assertion_id)` but no bitemporal columns. This means stance changes cannot be tracked historically. An investigator cannot see the evolution of evidence evaluation.

**Proposed Resolution**: Requires **ADR-012**.
- Add `tx_start TIMESTAMPTZ NOT NULL DEFAULT now()` to hypothesis_support
- Add `tx_end TIMESTAMPTZ NULL` to hypothesis_support
- Add `assigned_by UUID FK→civix_user NULL` (already present — good)
- Change `UNIQUE(hypothesis_id, assertion_id)` to `UNIQUE(hypothesis_id, assertion_id, tx_start)`
- Add rule: when stance changes, set tx_end on old row, insert new row

**Human Authorization Required**: YES.

---

### BLK-07
**Gap ID**: GAP-34  
**Severity**: HIGH  
**Status**: NEEDS_DECISION  
**Description**: `evidence_instance.case_id NOT NULL` means evidence cannot be ingested before a case exists. This is an operational constraint that must be explicitly documented and accepted.

**Options**:
- A. Accept: Always create a case first. Define a standard "STAGING" case for initial ingestion.
- B. Relax: Make `case_id` nullable on `evidence_instance`. Case association happens later.
- C. Add a separate `evidence_staging` table for pre-case evidence.

**Human Authorization Required**: YES.

---

### BLK-08
**Gap ID**: GAP-35  
**Severity**: HIGH  
**Status**: PROPOSED  
**Description**: `case_access UNIQUE(case_id, user_id)` prevents permission level history. Re-granting access at a different level requires UPDATE (losing history) or DELETE+INSERT (constraint violation if old row exists).

**Proposed Resolution**: Change UNIQUE to a partial unique index:
```sql
CREATE UNIQUE INDEX uq_case_access_active
ON civix.case_access(case_id, user_id)
WHERE is_revoked = FALSE;
```
This allows multiple historical rows for the same (case_id, user_id) as long as only one is active.

**Human Authorization Required**: YES — constraint change.

---

### BLK-09
**Gap ID**: GAP-37  
**Severity**: HIGH  
**Status**: NEEDS_DECISION  
**Description**: `civix_user` has a single `role civix_role_enum` column. In real operations, a user may have different capabilities in different contexts (SUPERVISOR in one department, READ_ONLY in another).

**Options**:
- A. Accept single role: Global role determines max capability. Case access restricts visibility. Simplest design.
- B. Add `civix.user_role_assignment(user_id, role, scope_type, scope_id)` for multi-role support.

**Human Authorization Required**: YES. Option A is recommended for MVP.

---

### BLK-10
**Gap ID**: GAP-39  
**Severity**: HIGH  
**Status**: NEEDS_DECISION  
**Description**: Expungement flow does not address free-text PII in `observation.observation_text`, `investigative_lead.lead_text`, `hypothesis.hypothesis_text`, `assertion.object_value`. These fields may contain the expunged person's name or other PII as literal text.

**Options**:
- A. Redaction: On expungement, NULL out or replace text in affected rows with "[REDACTED]".
- B. Accepted risk: Accept that text fields may contain residual PII; RLS restricts access to the entity record itself.
- C. Structured-only: Ban free text from lead_text and observation_text; force structured references (entity_id) instead. (Major design change.)

**Human Authorization Required**: YES — significant legal implication.

---

### BLK-11
**Gap ID**: GAP-40  
**Severity**: HIGH  
**Status**: NEEDS_DECISION  
**Description**: CCTV footage requires structured metadata (camera location, coverage area, recording interval, frame rate) that is not captured by a generic `evidence_artifact`. The current model treats CCTV recordings as just another file blob.

**Options**:
- A. Extend `evidence_artifact` with a JSONB `media_metadata` column for type-specific metadata.
- B. Create a `civix.cctv_artifact` extension table with specific fields.
- C. Use `observation.structured_content JSONB` to capture camera metadata per observation.

**Recommendation**: Option A (JSONB metadata column on evidence_artifact) for MVP. Full normalization deferred to Phase 2 forensics expansion.

**Human Authorization Required**: YES.

---

### BLK-12
**Gap ID**: GAP-51  
**Severity**: HIGH  
**Status**: PROPOSED  
**Description**: Intelligence reports have `classification: "Secret"`. There is no `classification_level` field on `civix.source` or `civix.evidence_artifact`. The clearance system in `10_SECURITY_RBAC_AUDIT_BIBLE.md` mentions classification but has no DB column to store it.

**Proposed Resolution**: Add `classification_level clearance_enum NULL DEFAULT 'UNCLASSIFIED'` to `civix.evidence_artifact`. Sources with a classification level should have their associated evidence_artifact auto-classified at the same level.

**Human Authorization Required**: YES — schema addition.

---

### BLK-13
**Gap ID**: GAP-52  
**Severity**: HIGH  
**Status**: PROPOSED  
**Description**: `civix.observation.observed_by UUID FK→civix_user NULL` cannot represent a field officer (P-28) who is a world Person but may not be a CIVIX application user.

**Proposed Resolution**: Requires **ADR-015**.  
Add `observer_entity_id UUID FK→entity NULL` to `civix.observation`.

Rules:
- If observer is a CIVIX system user AND a known person: populate both `observed_by` (user account) and `observer_entity_id` (person entity).
- If observer is a field officer who is not a CIVIX user: populate only `observer_entity_id`.
- If automated sensor: populate neither (use `observer_type` ENUM to indicate sensor type).

**Human Authorization Required**: YES.

---

### BLK-14
**Gap ID**: GAP-61  
**Severity**: HIGH  
**Status**: PROPOSED  
**Description**: `civix_generator/world/validators.py` uses default values for vehicles (18) and accounts (24) that contradict `config.py` frozen values (vehicles: 13, accounts: 29).

**Proposed Resolution**: Update `validators.py` to use `config.py` EXPECTED_COUNTS as the source of truth, not hard-coded defaults. This does NOT require modifying frozen files — only the validator logic.

```python
from config import EXPECTED_COUNTS
# Then use: EXPECTED_COUNTS.get("vehicles", 0) instead of 18
```

**Human Authorization Required**: NO — this is a bug fix in the test code, not a frozen artifact change.

---

## MEDIUM BLOCKERS

### BLK-15
**Gap ID**: GAP-41 through GAP-48  
**Severity**: MEDIUM  
**Status**: PROPOSED  
**Description**: Multiple TEXT fields that have a defined controlled vocabulary are not actual ENUM types. They are TEXT columns with parenthetical comments.

Fields affected:
| Column | Table | Status |
|---|---|---|
| `observer_type` | observation | TEXT → `observer_type_enum` |
| `observation_type` | observation | TEXT → `observation_type_enum` |
| `agency_type` | source | TEXT → `source_agency_type_enum` |
| `holder_role` | account_holder | TEXT → `account_holder_role_enum` |
| `gender` | person | TEXT → `gender_enum` |
| `severity` | data_quality_issue | TEXT → `issue_severity_enum` |
| `scope` | legal_restriction | TEXT → `restriction_scope_enum` |
| `status` | legal_restriction | TEXT → `restriction_status_enum` |
| `legal_status` | evidence_instance | TEXT → `evidence_legal_status_enum` |
| `device_type` | device | TEXT → `device_type_enum` |
| `property_type` | property | TEXT → `property_type_enum` |
| `number_type` | phone_number | TEXT → `phone_number_type_enum` |

**Proposed Resolution**: Define all missing ENUMs in Migration 02. Values derived from existing comments and domain knowledge.

**Human Authorization Required**: YES — confirm exact values for each ENUM before DDL.

---

### BLK-16
**Gap ID**: GAP-49  
**Severity**: MEDIUM  
**Status**: PROPOSED  
**Description**: `civix.provenance` has no index strategy. Recursive provenance traversal without indexes on `(derived_id, derived_type)` and `(source_id, source_type)` will be catastrophically slow.

**Proposed Resolution**: Add to Migration 18 (indexes):
```sql
CREATE INDEX idx_provenance_derived ON civix.provenance(derived_id, derived_type);
CREATE INDEX idx_provenance_source ON civix.provenance(source_id, source_type);
```

**Human Authorization Required**: NO — index additions have no semantic impact.

---

### BLK-17
**Gap ID**: GAP-25 (object_location_id on assertion)  
**Severity**: MEDIUM  
**Status**: PROPOSED  
**Description**: `assertion.object_location_id` is redundant because location is already addressable via `object_entity_id` (since location is a subtype of entity). Having both creates two ways to reference the same location, leading to inconsistency.

**Proposed Resolution**: Remove `object_location_id` from assertion. Update the CHECK constraint:
```sql
CHECK (object_entity_id IS NOT NULL OR object_value IS NOT NULL)
```
(Three-way check becomes two-way.)

**Human Authorization Required**: YES — schema simplification with semantic impact.

---

### BLK-18
**Gap ID**: GAP-27 (case_entity_role temporal)  
**Severity**: MEDIUM  
**Status**: PROPOSED  
**Description**: `case_entity_role` uses DATE fields instead of TIMESTAMPTZ, and lacks `tx_start/tx_end`. Role transitions within a day cannot be precisely tracked.

**Proposed Resolution**: 
- Change `valid_from DATE NULL` → `valid_from TIMESTAMPTZ NULL`
- Change `valid_to DATE NULL` → `valid_to TIMESTAMPTZ NULL`
- Add `tx_start TIMESTAMPTZ NOT NULL DEFAULT now()`
- Add `tx_end TIMESTAMPTZ NULL`

**Human Authorization Required**: YES — schema change.

---

### BLK-19
**Gap ID**: GAP-54 (ADR-021 dangling reference)  
**Severity**: LOW  
**Status**: PROPOSED  
**Description**: `03_DATABASE_SCHEMA_BIBLE.md` line 444 references "ADR-021" which does not exist.

**Proposed Resolution**: Change "(ADR-021, see `05_EPISTEMIC_MODEL.md`)" to "(ADR-011 proposed; see `05_EPISTEMIC_MODEL.md`)" until ADR-011 is formally written.

**Human Authorization Required**: NO.

---

### BLK-20
**Gap ID**: GAP-55 (test path hard-coded)  
**Severity**: LOW  
**Status**: PROPOSED  
**Description**: `test_world.py` hard-codes developer's machine path.

**Proposed Resolution**: Change to use relative path or environment variable. This is a one-line code fix and does not affect frozen artifacts.

**Human Authorization Required**: NO.

---

## Summary Table

| Blocker | Gap IDs | Severity | Status |
|---|---|---|---|
| BLK-01 | GAP-26 to GAP-30 | CRITICAL | PROPOSED |
| BLK-02 | GAP-31 | CRITICAL | NEEDS_DECISION |
| BLK-03 | GAP-32 | CRITICAL | PROPOSED |
| BLK-04 | GAP-38 | CRITICAL | PROPOSED |
| BLK-05 | GAP-60 | CRITICAL | NEEDS_DECISION |
| BLK-06 | GAP-33 | HIGH | PROPOSED |
| BLK-07 | GAP-34 | HIGH | NEEDS_DECISION |
| BLK-08 | GAP-35 | HIGH | PROPOSED |
| BLK-09 | GAP-37 | HIGH | NEEDS_DECISION |
| BLK-10 | GAP-39 | HIGH | NEEDS_DECISION |
| BLK-11 | GAP-40 | HIGH | NEEDS_DECISION |
| BLK-12 | GAP-51 | HIGH | PROPOSED |
| BLK-13 | GAP-52 | HIGH | PROPOSED |
| BLK-14 | GAP-61 | HIGH | PROPOSED (no auth needed) |
| BLK-15 | GAP-41 to GAP-48 | MEDIUM | PROPOSED |
| BLK-16 | GAP-49 | MEDIUM | PROPOSED (no auth needed) |
| BLK-17 | GAP-25 | MEDIUM | PROPOSED |
| BLK-18 | GAP-27 | MEDIUM | PROPOSED |
| BLK-19 | GAP-54 | LOW | PROPOSED (no auth needed) |
| BLK-20 | GAP-55 | LOW | PROPOSED (no auth needed) |

**CRITICAL: 5** | **HIGH: 9** | **MEDIUM: 4** | **LOW: 2**
**NEEDS_DECISION: 5** | **PROPOSED: 15**
