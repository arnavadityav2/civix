# A — ARCHITECTURE RECONCILIATION REPORT
## CIVIX Phase 1 — Pre-DDL Architecture Audit

**Date**: 2026-08-29 | **Auditor**: Adversarial Architecture Review Agent | **Status**: FINAL

---

## 1. Source-of-Truth Hierarchy Applied

In order of authority used during this audit:

1. Explicitly approved ADRs (ADR-001 through ADR-010 in `CIVIX_CHANGE_CONTROL.md`)
2. Current canonical CIVIX Bibles (`docs/*.md`)
3. Frozen synthetic-world specification (`synthetic_world.md` — stored in brain artifact dir)
4. Validated synthetic-world constraints (`config.py`, `validators.py`)
5. Existing generator implementation (`civix_generator/`)
6. Existing test suite (`tests/`)
7. Previous agent conclusions (lowest authority)

---

## 2. Documents & Code Reviewed

### Documentation Files Read (Cold)
- All 24 files in `docs/` — VERIFIED FROM FILE
- `CIVIX_CHANGE_CONTROL.md` — VERIFIED FROM FILE
- `21_KNOWN_GAPS_AND_RISKS.md` — VERIFIED FROM FILE

### Code Files Read
- `civix_generator/config.py` — VERIFIED FROM CODE
- `civix_generator/world/models.py` — VERIFIED FROM CODE
- `civix_generator/world/validators.py` — VERIFIED FROM CODE
- `civix_generator/lineage/lineage.py` — VERIFIED FROM CODE
- `civix_generator/tests/test_world.py` — VERIFIED FROM CODE
- `database/schema_postgres.sql` — VERIFIED FROM CODE (superseded)

### Output Data Inspected
- `output/cdrs.csv` (385 rows) — VERIFIED FROM FILE
- `output/transactions.csv` (50 rows) — VERIFIED FROM FILE
- `output/property_transfers.csv` (3 rows) — VERIFIED FROM FILE
- `output/criminal_history_records.csv` (6 rows) — VERIFIED FROM FILE
- `output/surveillance_reports.json` (12 reports) — VERIFIED FROM FILE
- `output/intelligence_reports.json` (5 reports) — VERIFIED FROM FILE
- `output/ground_truth.json` — VERIFIED FROM FILE: EMPTY `{}` ← CRITICAL FINDING

---

## 3. Critical Findings Summary

### FINDING-01 — ground_truth.json Is Empty [CRITICAL]
**Status**: VERIFIED FROM FILE  
`output/ground_truth.json` contains only `{}` — two bytes. It is completely empty.

The documentation in `12_SYNTHETIC_DATA_BIBLE.md` states: "ground_truth JSONB is NEVER projected to Neo4j and NEVER included in ML feature extraction." It is treated as an important frozen artifact. But the file itself contains NO ground truth data.

**Impact**: ML validation, scenario evaluation, and Phase 5 ingestion verification are all designed around comparing against `ground_truth.json`. If it is empty, none of those validations can work.

**Action required**: Determine whether ground_truth.json is intentionally empty (placeholder) or was accidentally left empty. This must be clarified before Phase 5 begins.

---

### FINDING-02 — Validator Count Mismatch: Vehicles [HIGH]
**Status**: VERIFIED FROM CODE vs VERIFIED FROM CODE  
**CONFLICT**:
- `config.py` (FROZEN): `"vehicles": 13`
- `validators.py` (code): `expected = world.expected_counts.get('vehicles', 18)` — default is 18
- `12_SYNTHETIC_DATA_BIBLE.md`: "Vehicles: 13"

`validators.py` uses default `18` if the world doesn't set expected_counts. The frozen `config.py` says `13`. If the world's `expected_counts` dict is empty or doesn't include `vehicles`, the validator will pass a world with 18 vehicles when only 13 are expected.

**Action required**: Align validator defaults with config.py. This is a test correctness bug.

---

### FINDING-03 — Validator Count Mismatch: Accounts [HIGH]
**Status**: VERIFIED FROM CODE vs VERIFIED FROM CODE  
**CONFLICT**:
- `config.py` (FROZEN): `"accounts": 29`
- `validators.py`: `expected = world.expected_counts.get('accounts', 24)` — default is 24

Same problem as FINDING-02. The defaults are stale.

**Action required**: Align validator defaults with config.py.

---

### FINDING-04 — `hypothesis_status_enum` Referenced But Not Defined [CRITICAL]
**Status**: VERIFIED FROM FILE  
`03_DATABASE_SCHEMA_BIBLE.md` at line 479 references `hypothesis_status_enum` in the hypothesis table definition:
```
`status` hypothesis_status_enum NOT NULL DEFAULT 'ACTIVE'
```
But the ENUM Types section (lines 35-117) does NOT define `hypothesis_status_enum`.

Neither does any other Bible.

**Impact**: DDL implementor cannot create this ENUM. They would either invent values arbitrarily or use a different type.

**Allowed values**: ACTIVE, ARCHIVED, CONFIRMED, REFUTED — must be explicitly defined.

**Action required**: Define `hypothesis_status_enum` in the schema Bible.

---

### FINDING-05 — `lead_priority_enum` and `lead_status_enum` Referenced But Not Defined [CRITICAL]
**Status**: VERIFIED FROM FILE  
`03_DATABASE_SCHEMA_BIBLE.md` at line 491 references `lead_priority_enum` and `lead_status_enum` in the investigative_lead definition. Neither is defined in the ENUM section.

**Impact**: Same as FINDING-04 — DDL implementor must invent values.

**Expected values**:
- `lead_priority_enum`: CRITICAL, HIGH, MEDIUM, LOW
- `lead_status_enum`: OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED

**Action required**: Define both ENUMs in the schema Bible.

---

### FINDING-06 — `task_type_enum` and `task_status_enum` Referenced But Not Defined [CRITICAL]
**Status**: VERIFIED FROM FILE  
`investigation_task` (line 495) references `task_type_enum` and `task_status_enum`. Neither defined.

**Expected values**:
- `task_type_enum`: INTERVIEW, SURVEILLANCE, SEARCH_AND_SEIZURE, FORENSIC_COLLECTION, FINANCIAL_REVIEW, LEGAL_REQUEST, COURT_ORDER, DATA_ANALYSIS, FIELD_VERIFICATION, OTHER
- `task_status_enum`: PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED

**Action required**: Define both ENUMs in the schema Bible.

---

### FINDING-07 — `hypothesis_status_enum` Values Create Semantic Ambiguity [HIGH]
**Status**: ARCHITECTURAL INFERENCE  
The `hypothesis` table has `confirmed_by UUID FK NULL` with the CHECK constraint `status != 'CONFIRMED' OR confirmed_by IS NOT NULL`. But the Bible never defines what `ARCHIVED` means vs `CLOSED` vs `REFUTED` for a hypothesis. Can a hypothesis be `REFUTED` vs `CONFIRMED`? Is `ARCHIVED` different from `CLOSED`? These are different investigative states.

**Action required**: Define precise semantic meanings for each hypothesis status value.

---

### FINDING-08 — `source_identity` Has Circular FK to `extraction` [HIGH]
**Status**: VERIFIED FROM FILE  
`civix.source_identity` has `extraction_id UUID FK→extraction` (line 220). But `civix.extraction` has `instance_id FK→evidence_instance`. This creates an ordering problem: you need to create an extraction before the source_identity, but extractions typically reference an existing source_identity they extracted.

**Actual issue**: A source_identity can come from either a raw ingest (no extraction) OR an AI extraction process. If it comes from raw ingest, `extraction_id = NULL` is fine. But the FK implies extraction was the source — this conflates two separate origins.

**The correct design**: Provenance of how the source_identity was discovered should live in `civix.provenance`, not as a nullable FK on source_identity itself. The `extraction_id` column on source_identity is architecturally wrong — it's a provenance shortcut that bypasses the provenance table.

**Action required**: Remove `extraction_id` from `source_identity`. Instead, use `provenance(derived_type='SOURCE_IDENTITY', source_type='EXTRACTION')` if AI-extracted. This is consistent with ADR-006.

---

### FINDING-09 — `event_participant` UNIQUE Constraint Blocks Same Entity Multiple Roles [HIGH]
**Status**: VERIFIED FROM FILE  
`event_participant` has `UNIQUE(event_id, entity_id, participant_role)`. This is correct.

But consider: a property mutation event where PROP-01 is both the TARGET_PROPERTY being transferred AND has a role as something else — this is fine. But what about a person who is both a WITNESS and an OFFICER at the same surveillance event? That should be allowed and the UNIQUE constraint permits it (different roles).

However, consider: SURV-000001 observes BOTH P-03 and P-09 at the same location. That's two entities at the same event — allowed. But what if the observing officer (P-28) is both OBSERVER (as officer) and needs to appear as SUBJECT? The UNIQUE constraint allows both as different roles.

**Verdict**: UNIQUE(event_id, entity_id, participant_role) is CORRECT and handles all cases properly. This is PASS.

---

### FINDING-10 — `observation` Table Has No FK to `event` [MEDIUM]
**Status**: VERIFIED FROM FILE  
The epistemic pipeline says `Observation → Event`. But `civix.observation` has only `instance_id FK→evidence_instance`. There is no FK from observation to event, and no FK from event to observation.

The provenance table is supposed to bridge this. But that means: to find "which observation produced this event," you must traverse the provenance table using type+id lookup (no DB FK). This is an application-level query.

**The real question**: Is the direction Observation→Event or Evidence→Event directly? The Bible shows them as parallel paths from Evidence. But then how does an Event get created? From Observations AND/OR Extractions, via provenance records.

**Impact**: DDL implementor has no FK to follow. They must use `civix.provenance` to link observations to events. This is correct per ADR-006 but must be explicitly documented in `05_EPISTEMIC_MODEL.md`.

**Action required**: Explicitly document in `05_EPISTEMIC_MODEL.md` that observation→event linkage lives in `civix.provenance`, not as a direct FK.

---

### FINDING-11 — `evidence_instance` Cannot Exist Without `case_id` (Circular Dependency) [HIGH]
**Status**: VERIFIED FROM FILE  
`evidence_instance` has `case_id UUID NOT NULL FK→investigative_case`. This means you cannot create an evidence_instance without first having a case.

But consider: a source (telecom provider) submits a CDR batch. The CDR batch is evidence. But which case does it belong to? In many real investigations, raw data arrives BEFORE a formal case is created. The current schema forces a case to exist first.

**Impact**: This creates an ordering constraint that may not match operational reality. Also, what if the CDR batch is relevant to multiple cases? The current design correctly creates one `evidence_instance` per case. But this means you cannot ingest evidence without a case — an `evidence_artifact` without any `evidence_instance` is an orphan with no case context.

**Proposed resolution**: Either (a) accept this constraint and require cases to be created before ingestion, OR (b) allow a special "staging" case for pre-case evidence. Document this as a required operational decision.

**Action required**: Document explicitly in `05_EPISTEMIC_MODEL.md` and `03_DATABASE_SCHEMA_BIBLE.md` that evidence ingestion REQUIRES a pre-existing case.

---

### FINDING-12 — `hypothesis_support` UNIQUE Constraint Prevents Revising Stance [HIGH]
**Status**: VERIFIED FROM FILE  
`hypothesis_support` has `UNIQUE(hypothesis_id, assertion_id)`. This means only ONE stance record can exist for any (hypothesis, assertion) pair at any time.

**Problem**: What if an analyst initially marks assertion A1 as SUPPORT for hypothesis H1, then later reassesses and marks it NEUTRAL? Under the current UNIQUE constraint, you cannot insert a second row. You must UPDATE the existing row — but this loses the historical record of the original stance assessment.

**The schema has no `tx_start/tx_end` on `hypothesis_support`**. There is no bitemporal versioning on stance assessments. This means stance changes are irreversible mutations with no audit trail.

**Action required**: Add `tx_start TIMESTAMPTZ NOT NULL DEFAULT now()` and `tx_end TIMESTAMPTZ NULL` to `hypothesis_support`. Change UNIQUE to `UNIQUE(hypothesis_id, assertion_id, tx_start)`. Or use a supersession pattern similar to `identity_resolution`.

---

### FINDING-13 — `claim_link` Between Event and Assertion Is Undefined [MEDIUM]
**Status**: VERIFIED FROM FILE  
The epistemic model says:
```
Event → (via provenance) → Assertion
```
But there is no direct structural link. The `civix.event` table has no `assertion_id`. The `civix.assertion` table has no `event_id`. The link is supposed to go through `civix.provenance`.

**But**: `civix.provenance` uses application-enforced FKs (ADR-006). So the linkage from Event to Assertion has NO database-level referential integrity.

**Deeper issue**: An assertion like "P-01 CALLED P-02" should be provenance-linked to a CALL event. But there is no schema mechanism to enforce this link. An assertion can exist with no event provenance at all.

**Action required**: Document that provenance completeness is enforced by integration tests, not DB constraints. This is an accepted architectural risk (ADR-006) but must be explicitly called out in `18_TESTING_VALIDATION_BIBLE.md`.

---

### FINDING-14 — Intelligence Reports Cannot Be Properly Ingested [HIGH]
**Status**: VERIFIED FROM FILE vs VERIFIED FROM FILE  
`intelligence_reports.json` has this structure:
```json
{
  "source": "Confidential Informant",
  "classification": "Secret",
  "narrative": "...",
  "entities_mentioned": ["P-05"],
  "locations_mentioned": [],
  "cases_mentioned": []
}
```

**Problems**:
1. `entities_mentioned` contains canonical world IDs like `"P-05"`. But the CIVIX database does not use canonical world IDs as primary keys. During ingestion, P-05 must be resolved to a `source_identity` or `person` entity_id. The mapping mechanism is undefined.

2. `locations_mentioned` and `cases_mentioned` are always empty arrays in the actual data. If they were populated, what entity types do they reference? Location IDs? Case numbers? This is undefined.

3. The `classification: "Secret"` field maps to `clearance_enum` on the user side, but there is no `classification` field on `evidence_artifact` or `source`. The `source` table has no `classification_level` field.

**Action required**: 
- Add `classification_level clearance_enum NULL` to `civix.source` or `civix.evidence_artifact`.
- Document the mapping from canonical world person IDs to database entity IDs during ingestion.

---

### FINDING-15 — Surveillance Reports Reference `location_id` With LOC- Prefix [HIGH]
**Status**: VERIFIED FROM FILE  
Surveillance reports reference `"location_id": "LOC-13"`, `"LOC-17"`, etc. These are canonical world location IDs.

But `civix.location` is an entity subtype — its PK is a UUID, not `LOC-13`. The `location_id` in the JSON is a world-level identifier, not a database entity_id.

**Impact**: The ingestion pipeline must map `LOC-13` → some location UUID. But:
1. There is no mapping table defined.
2. The canonical world location definitions (geometry, type, name) must come from somewhere.
3. `LOC-01` through `LOC-30` must become PostGIS geometry entries in `civix.location`. Where are the actual coordinates? The canonical world does not appear to contain coordinates for LOC-* entities (only the location_id strings).

**Action required**: Document where LOC-* coordinates come from. If approximate, define the fallback (ESTIMATED_POINT + uncertainty). Create a canonical location ID → database entity mapping plan.

---

### FINDING-16 — `has_observation_type_enum` Missing for Observation [MEDIUM]
**Status**: VERIFIED FROM FILE  
`civix.observation` has `observer_type TEXT NOT NULL` and `observation_type TEXT NULL`. Both are free-text. Given the stated principle (INV-18: free-text predicates are banned), these should be controlled vocabularies.

**Expected `observer_type` values**: HUMAN_OFFICER, SENSOR_CCTV, SENSOR_SIGNAL, AI_EXTRACTION, AUTOMATED_SYSTEM, INFORMANT
**Expected `observation_type` values**: PHYSICAL_SURVEILLANCE, CDR_OBSERVATION, FINANCIAL_OBSERVATION, VEHICLE_SIGHTING, FORENSIC_OBSERVATION, DOCUMENT_OBSERVATION, INTELLIGENCE_REPORT

**Action required**: Define `observer_type_enum` and `observation_type_enum` in the schema Bible.

---

### FINDING-17 — `source.agency_type` Is Free-Text Despite Being Enumerable [MEDIUM]
**Status**: VERIFIED FROM FILE  
`civix.source` has `agency_type TEXT NOT NULL` with a comment: `ENUM: TELECOM, BANK, POLICE, COURT, REVENUE_OFFICE, INFORMANT, CCTV_SYSTEM, HOSPITAL, FORENSIC_LAB, OSINT, OTHER`.

This should be an actual ENUM type, not TEXT with a comment.

**Action required**: Define `source_agency_type_enum` in the schema Bible and use it on the `source` table.

---

### FINDING-18 — `account_holder.holder_role` Is Free-Text [MEDIUM]
**Status**: VERIFIED FROM FILE  
`account_holder.holder_role TEXT NOT NULL (PRIMARY/JOINT/AUTHORIZED_SIGNATORY/POA/NOMINEE/CORPORATE_DIRECTOR)` — described as free-text with a parenthetical comment listing values.

**Action required**: Define `account_holder_role_enum` and use it.

---

### FINDING-19 — `person.gender` Is Free-Text Despite Fixed Values [LOW]
**Status**: VERIFIED FROM FILE  
`person.gender TEXT NULL` with comment `ENUM: MALE, FEMALE, OTHER, UNDISCLOSED`. Should be an actual ENUM.

**Action required**: Define `gender_enum`.

---

### FINDING-20 — `data_quality_issue.severity` Is Free-Text [MEDIUM]
**Status**: VERIFIED FROM FILE  
`severity TEXT NOT NULL (CRITICAL/HIGH/MEDIUM/LOW/INFO)`. Should be `severity_enum`.

**Action required**: Define `issue_severity_enum`.

---

### FINDING-21 — `legal_restriction.scope` and `status` Are Free-Text [MEDIUM]
**Status**: VERIFIED FROM FILE  
`scope TEXT NOT NULL` and `status TEXT NOT NULL DEFAULT 'ACTIVE'` on `legal_restriction`.

`10_SECURITY_RBAC_AUDIT_BIBLE.md` defines: `scope: FULL_RECORD | IDENTITY_ONLY | CONTENT_ONLY | ANALYTICAL_ONLY` and `status: ACTIVE | LIFTED | EXPIRED`. These should be ENUMs.

**Action required**: Define `restriction_scope_enum` and `restriction_status_enum`.

---

### FINDING-22 — `evidence_instance.legal_status` Is Free-Text [MEDIUM]
**Status**: VERIFIED FROM FILE  
`legal_status TEXT NOT NULL DEFAULT 'ACTIVE'` with comment `ENUM: ACTIVE, RESTRICTED, SEALED, EXPUNGED`. Should be an actual ENUM.

**Action required**: Define `evidence_legal_status_enum`.

---

### FINDING-23 — `civix_user` Has Only ONE Role Per User [HIGH]
**Status**: VERIFIED FROM FILE  
`civix_user.role civix_role_enum NOT NULL` — a single role column.

**Problem**: In practice, an investigator may be a SUPERVISOR in Unit A and an INVESTIGATOR in Unit B. Or they may be a FORENSIC_EXAMINER globally but READ_ONLY on financial cases. A single `role` column cannot represent this.

Furthermore, `case_access.permission_level` (READ/WRITE/ADMIN) already provides per-case access. But the global `role` on `civix_user` is used to determine what capabilities the user has system-wide (e.g., can create hypotheses, can manage restrictions).

**The conflict**: Role determines capability. Case access determines case visibility. These are two different access dimensions. The current design conflates them by putting a single role on the user globally.

**Proposed resolution**: Accept that `civix_user.role` is the *primary* system role, and `case_access` provides the per-case override. Document this explicitly. OR: Change `civix_user.role` to an array or create a separate `civix.user_role_assignment` table for multi-role support.

**Action required**: Decision required. Document in `10_SECURITY_RBAC_AUDIT_BIBLE.md`.

---

### FINDING-24 — `case_access` UNIQUE Constraint Prevents Permission Level Changes [HIGH]
**Status**: VERIFIED FROM FILE  
`case_access` has `UNIQUE(case_id, user_id)`. This means only ONE access record per user per case. To change a user's permission from READ to WRITE, you must UPDATE the row — losing history.

**The table has `is_revoked` and `revoked_at`, implying a revoke-and-recreate pattern. But the UNIQUE constraint prevents creating a new access row while the old one exists (even if revoked is TRUE).

**Action required**: Either (a) change UNIQUE to `UNIQUE(case_id, user_id) WHERE is_revoked = FALSE` (a partial unique index), OR (b) make revocation set `is_revoked = TRUE` and then allow a new row to be inserted. A partial unique index on the active record is the correct approach.

---

### FINDING-25 — `assertion.object_location_id` FK to `location` Redundant With `object_entity_id` [MEDIUM]
**Status**: VERIFIED FROM FILE  
`civix.assertion` has BOTH:
- `object_entity_id UUID FK→entity NULL` — for any entity object
- `object_location_id UUID FK→location NULL` — specifically for spatial assertions

But `location` IS a subtype of `entity`. So `object_entity_id` can already reference a location (since `location.entity_id FK→entity`). The `object_location_id` column is redundant — it points to a table that is already addressable via `object_entity_id`.

**The only reason to have both**: type safety — `object_location_id` guarantees the FK target is specifically a location entity, while `object_entity_id` could point to any entity type.

**Resolution**: Remove `object_location_id` from assertion. Use `object_entity_id` and rely on the entity_type discriminator. This simplifies the schema without losing expressiveness.

**Action required**: Remove `object_location_id` from assertion. Update the CHECK constraint accordingly.

---

### FINDING-26 — `provenance` Table Has No Index Strategy [MEDIUM]
**Status**: ARCHITECTURAL INFERENCE  
`civix.provenance` is the foundation for recursive chain traversal. The query pattern is:
```sql
WHERE derived_id = $id AND derived_type = 'ASSERTION'
```
There is no compound index defined on `(derived_id, derived_type)` in the schema Bible. For recursive provenance traversal over millions of rows, this will be catastrophically slow without an index.

**Action required**: Add explicit `CREATE INDEX ON civix.provenance (derived_id, derived_type)` and `(source_id, source_type)` to Migration 18.

---

### FINDING-27 — `case_entity_role` Lacks Temporal Versioning [MEDIUM]
**Status**: VERIFIED FROM FILE  
`case_entity_role` has `valid_from DATE NULL` and `valid_to DATE NULL` — nullable date-level validity, not a TSTZRANGE.

**Problem**: A person's role in a case may change (PERSON_OF_INTEREST → SUSPECT → ACCUSED → ACQUITTED). The `valid_from/valid_to` fields allow this, but:
1. They are DATE, not TIMESTAMPTZ. Criminal role transitions can happen intra-day.
2. There is no `tx_start/tx_end` for bitemporal tracking (when did CIVIX record this role change?).
3. The UNIQUE constraint `UNIQUE(case_id, entity_id, role)` means you cannot have a person be SUSPECT twice (if they are acquitted and then re-charged). You'd need to rely on `valid_to` date changes.

**Action required**: Add `tx_start TIMESTAMPTZ NOT NULL DEFAULT now()` and `tx_end TIMESTAMPTZ NULL` to `case_entity_role`. Change date fields to TIMESTAMPTZ. Adjust UNIQUE to partial unique or composite with temporal.

---

### FINDING-28 — Neo4j Node Label `:Assertion` Creates Problematic Graph Topology [HIGH]
**Status**: VERIFIED FROM FILE — `13_NEO4J_GRAPH_BIBLE.md`  
The graph bible projects `Assertion` as a Neo4j node. This creates a **hypergraph** structure where:
- Entity nodes → `[:ASSERTED_BY]` → `:Assertion` node → `[:ASSERTS]` → Entity nodes

This means a call from P-01 to P-02 becomes: `P-01 →[:ASSERTED_BY]→ Assertion-A1 →[:ASSERTS]→ P-02`. A standard 2-hop traversal from P-01 to P-02 now requires 3 hops (P-01 → Assertion → P-02). Every graph algorithm becomes more expensive.

**For PageRank**: Central assertion nodes can distort entity centrality scores. Assertions with many hypothesis_support relationships will appear "central" in the graph even though they are intermediate nodes.

**More critically**: What does "path from P-01 to P-09" mean when assertions are intermediate nodes? Is a 2-hop path (P-01 → Assert → P-09) a "direct connection"? What about P-01 → Assert-A1 → Hypothesis → Assert-A2 → P-09? These path semantics are undefined.

**Action required**: Define explicit graph traversal semantics for the assertion-as-node design. Alternatively, consider a dual projection: (a) entity-event graph (no assertions) for structural algorithms, (b) full epistemic graph (with assertions) for provenance traversal only. Document in `13_NEO4J_GRAPH_BIBLE.md`.

---

### FINDING-29 — `source_identity` TX fields lack immutability enforcement [MEDIUM]
**Status**: VERIFIED FROM FILE  
`source_identity` has `tx_start TIMESTAMPTZ NOT NULL` and `tx_end TIMESTAMPTZ NULL`, indicating bitemporal support. But the Bible states `raw_identifier is IMMUTABLE`. There is no trigger or constraint that prevents updating `raw_identifier`. The immutability is entirely application-enforced.

**Action required**: Add a PostgreSQL trigger on `source_identity` that raises an exception if `raw_identifier` is changed in an UPDATE operation (similar to the `audit_event` trigger).

---

### FINDING-30 — No `SIM` Table Cardinality in Golden World [MEDIUM]
**Status**: VERIFIED FROM CODE  
`config.py` does NOT have a count for SIM cards. `12_SYNTHETIC_DATA_BIBLE.md` says "SIM table cardinalities: STATUS: OPEN DECISION". The existing validator (`validators.py`) does not validate SIM count. The CDR data references ICCID values implicitly through the `caller_imei`/`receiver_imei` fields.

**Impact**: During ingestion, SIM entities must be created from CDR data, but there is no canonical count to validate against.

**Action required**: Either define SIM cardinality in the synthetic world or accept that SIM count is derived from CDR data.

---

### FINDING-31 — `test_world.py` Hard-codes an Absolute Path [LOW]
**Status**: VERIFIED FROM CODE  
`test_world.py` line 10:
```python
path = r"C:\Users\ARNAV ADITYA\.gemini\antigravity-ide\brain\4d2a421e-8d1d-4a48-8703-7eae27170647\synthetic_world.md"
```
This hard-codes the developer's machine path. The test cannot be run by any other contributor without modifying this line.

**Action required**: Use environment variable or relative path from repo root.

---

### FINDING-32 — `vehicle.entity_id` in `models.py` Conflicts with DB Entity_ID Design [MEDIUM]
**Status**: VERIFIED FROM CODE  
In `models.py`, `Vehicle.entity_id` is a string like `"P-03"` — it stores the OWNER's person ID, not the vehicle's own ID. This is confirmed by `test_world.py` line 74: `if v.entity_id == "P-03"`.

The `models.py` `Vehicle` dataclass uses `entity_id` to mean "owner_id." But in the database schema, `civix.vehicle.entity_id` is the vehicle's own UUID. The vehicle's owner is represented by an `assertion(OWNED/DRIVER_OF)` or `account_holder`.

**Impact**: During ingestion, the `Vehicle.entity_id` field from models.py must NOT be mapped to `civix.vehicle.entity_id`. It should inform the creation of an assertion like `Person(entity_id=P-03's UUID) OWNS Vehicle(entity_id=new UUID)`.

This semantic mismatch in the generator code will cause confusion during the ingestion implementation phase.

**Action required**: Document explicitly in `12_SYNTHETIC_DATA_BIBLE.md` that `Vehicle.entity_id` in the generator is the OWNER person ID, not the vehicle database entity ID.

---

### FINDING-33 — Surveillance Report Observer Ingestion Undefined [MEDIUM]
**Status**: VERIFIED FROM FILE  
Surveillance reports have `"observing_officer": "Constable Vijay Kumar (P-28)"`. This is a combined name+ID string. During ingestion, P-28 must become a `source_identity` or `person` reference. The ingestion logic for this field is undefined.

Furthermore, the `civix.observation` table has `observed_by UUID FK→civix_user NULL`. But the observing officer (P-28) is a Person in the world, not a CIVIX application user. P-28 is a Constable — presumably a CIVIX user — but may not have a `civix_user` account.

**The conflict**: `observation.observed_by` points to `civix_user`, but real-world observers may be field officers who are not CIVIX system users.

**Action required**: Either (a) allow `observed_by` to be NULL and use `event_participant(OBSERVER)` to record the observing officer entity, OR (b) add `observer_entity_id UUID FK→entity NULL` as an alternative to `observed_by` for non-system-user observers.

---

### FINDING-34 — `FIR` Table Missing Key Fields [MEDIUM]
**Status**: VERIFIED FROM FILE  
`civix.fir` has `complainant_entity_id FK→entity NULL`. But criminal_history_records.csv has `offence` (text) and `status` (text: "Fine Paid", "Acquitted"). The FIR table has no `status` field. Where does FIR status (open/closed/charge_sheeted) go?

Also: `sections_invoked TEXT[] NULL` — multiple sections invoked is correct (IPC/BNS sections), but using a TEXT array rather than a separate normalized table means sections cannot be queried/indexed efficiently.

**Action required**: 
- Add `fir_status TEXT NOT NULL DEFAULT 'OPEN'` (or enum) to `civix.fir`.
- Consider a separate `civix.fir_section` table instead of TEXT[] if section-level analytics are needed.

---

### FINDING-35 — ADR Reference "ADR-021" in Schema Bible [LOW]
**Status**: VERIFIED FROM FILE  
`03_DATABASE_SCHEMA_BIBLE.md` line 444 says:
```
**No entity FKs on event**: Location is an `event_participant(role=LOCATION)`. (ADR-021, see `05_EPISTEMIC_MODEL.md`)
```
But there is no ADR-021 in `CIVIX_CHANGE_CONTROL.md`. ADRs only go up to ADR-010. This is a dangling reference.

**Action required**: Either create ADR-011 (re-numbering was probably intended) or remove the reference.

---

### FINDING-36 — CONTRADICT Relationship in Neo4j Bible Is Self-Contradictory [HIGH]
**Status**: VERIFIED FROM FILE  
`13_NEO4J_GRAPH_BIBLE.md` says:
```
| `[:CONTRADICTS]` | `:Assertion` | `:Hypothesis` | weight, stance='CONTRADICT' | ⚠️ Property-based ONLY — never structural edge |
```

But this table ROW DEFINES A `[:CONTRADICTS]` RELATIONSHIP TYPE. If CONTRADICT is "never a structural edge," why is it listed as a relationship type in the relationship type table at all? The intent was that CONTRADICT stance is stored as a property on the `[:SUPPORTS]` relationship OR as a separate row that algorithms must filter. But the current text says `:CONTRADICTS` is a named relationship type that is simultaneously "not a structural edge."

This is contradictory. A named Cypher relationship type IS a structural edge in Neo4j's property graph model. You cannot have a relationship type called `[:CONTRADICTS]` that is "not structural."

**The correct design**: There should be ONE relationship type `[:HAS_STANCE]` with a `stance` property that can be SUPPORT, CONTRADICT, NEUTRAL, INCONCLUSIVE. Graph algorithms filter `WHERE r.stance = 'SUPPORT'`. There should NOT be separate `[:SUPPORTS]` and `[:CONTRADICTS]` relationship types.

**Action required**: Replace `[:SUPPORTS]` and `[:CONTRADICTS]` with a single `[:HAS_STANCE {stance, weight}]` relationship type. Update `13_NEO4J_GRAPH_BIBLE.md` accordingly.

---

### FINDING-37 — Expungement Does Not Address Derived Analytics [HIGH]
**Status**: VERIFIED FROM FILE  
`10_SECURITY_RBAC_AUDIT_BIBLE.md` Section 6.1 step 7 says: "Derived analytics (hypotheses, leads) that depended on the expunged entity are flagged for re-evaluation via data_quality_issue."

But this is incomplete. The actual problem is:
1. A lead was generated based on an assertion about P-99 (now expunged)
2. The lead text says "P-99 was seen near the crime scene at X time"
3. Even if P-99 is expunged, the lead TEXT may still contain PII
4. Similarly, assertion.object_value TEXT may contain the expunged person's name directly

The RLS policy on `evidence_instance` protects the evidence artifact. The entity node is deleted from Neo4j. But the lead text, assertion values, hypothesis text, and observation_text fields may all contain the expunged person's identifying information as free text.

**Action required**: Define how free-text fields are sanitized upon expungement. Options: (a) NULL out the text fields, (b) mark with a redaction marker, (c) accept this as a known limitation. Document the decision explicitly.

---

### FINDING-38 — Missing Media/CCTV Entity Model [HIGH]
**Status**: ARCHITECTURAL INFERENCE  
The audit mandate (Section 5) requires checking media entity support. The current architecture has `evidence_artifact` as a generic file store. But CCTV footage has specific metadata needs:
- Camera ID / camera location
- Coverage area (polygon)
- Recording start/end time
- Frame count, frame rate
- Whether footage has been reviewed
- Timestamps of detected events within the footage

A CCTV recording is not just a binary blob. It has structured observational metadata. The current `observation` table captures what was observed, but not the camera metadata.

**Action required**: Define a `civix.media_artifact_metadata` extension or a `civix.cctv_camera` entity subtype to carry camera-specific metadata. Alternatively, use `evidence_artifact` + structured metadata in `observation.structured_content JSONB`. Document the decision.

---

### FINDING-39 — No Entity for `SIM` Card in Generation World [MEDIUM]
**Status**: VERIFIED FROM CODE  
`models.py` has no `SIM` dataclass. `Device` has `sim_history: List[Dict]`, which is a list of SIM history records embedded in the device. There is no first-class SIM entity in the generator world model.

The CIVIX database schema defines `civix.sim` as a first-class entity. During ingestion, SIM entities must be created from the `sim_history` dictionaries in `Device` objects. But the structure of these dicts is undefined in the documentation.

**Action required**: Document the structure of `Device.sim_history` dict format and how it maps to `civix.sim` + `civix.sim_in_device` rows.

---

### FINDING-40 — `case_link.linked_object_type` and `linked_object_id` Are Polymorphic Without FK [MEDIUM]
**Status**: VERIFIED FROM FILE  
`civix.case_link` has `linked_object_type TEXT NOT NULL` and `linked_object_id UUID NOT NULL`. This is exactly the polymorphic type+id pattern that ADR-006 deferred to application-layer enforcement. But `case_link` is a different context than `provenance`.

Unlike provenance (which is explicitly documented as ADR-006), `case_link` polymorphism is not mentioned in any ADR. It silently uses the same pattern without documentation.

**Action required**: Either create ADR-011 for case_link polymorphism or replace `linked_object_type/linked_object_id` with explicit FK options per shareable object type.

---

## 4. Confirmed Gaps From Previous Register

All 19 previously "CLOSED" gaps were verified against the current schema Bible.

| Previous Gap | Verified Closed? | Notes |
|---|---|---|
| GAP-01 civix_user | ✅ CONFIRMED CLOSED | Table defined |
| GAP-02 case table | ✅ CONFIRMED CLOSED | investigative_case defined |
| GAP-03 data_quality_issue | ✅ CONFIRMED CLOSED | Table defined |
| GAP-04 evidence_instance.case_id | ✅ CONFIRMED CLOSED | Column present |
| GAP-05 merge/split events | ✅ CONFIRMED CLOSED | Both tables defined |
| GAP-06 sim_number_assignment | ✅ CONFIRMED CLOSED | Table + GIST defined |
| GAP-07 account_holder | ✅ CONFIRMED CLOSED | Table defined |
| GAP-08 case_entity_role | ✅ CONFIRMED CLOSED (partial) | Defined, but see FINDING-27 (no tx_start/tx_end) |
| GAP-09 case_access | ✅ CONFIRMED CLOSED (partial) | Defined, but see FINDING-24 (UNIQUE issue) |
| GAP-12 hash uniqueness | ✅ CONFIRMED CLOSED | UNIQUE(sha256_hash, hash_algorithm) |
| GAP-13 predicate vocabulary | ✅ CONFIRMED CLOSED | predicate_enum defined |
| GAP-14 confidential informant | ✅ CONFIRMED CLOSED | source.is_identity_protected |
| GAP-17 is_criminal | ✅ CONFIRMED CLOSED | Not in schema |
| GAP-18 vehicle-only sightings | ✅ CONFIRMED CLOSED | participant_role optional |
| GAP-19 org-name accounts | ✅ CONFIRMED CLOSED | source_identity mapping documented |
| GAP-20 UNKNOWN-IMEI | ✅ CONFIRMED CLOSED | source_identity mapping documented |
| GAP-21 event.location_id | ✅ CONFIRMED CLOSED | Location is event_participant |
| GAP-22 hypothesis constraint | ✅ CONFIRMED CLOSED | DB CHECK defined |
| GAP-23 CONTRADICT graph edges | ⚠️ PARTIALLY CLOSED | See FINDING-36 — the Neo4j design is self-contradictory |
| GAP-24 sim GIST exclusion | ✅ CONFIRMED CLOSED | GIST constraint defined |
| GAP-25 outbox table | ✅ CONFIRMED CLOSED | Table defined in Migration 13 |

---

## 5. New Gaps Discovered This Audit

| Gap ID | Finding | Severity |
|---|---|---|
| GAP-26 | hypothesis_status_enum not defined | CRITICAL |
| GAP-27 | lead_priority_enum not defined | CRITICAL |
| GAP-28 | lead_status_enum not defined | CRITICAL |
| GAP-29 | task_type_enum not defined | CRITICAL |
| GAP-30 | task_status_enum not defined | CRITICAL |
| GAP-31 | ground_truth.json is empty | CRITICAL |
| GAP-32 | source_identity.extraction_id is architecturally wrong | HIGH |
| GAP-33 | hypothesis_support has no bitemporal versioning | HIGH |
| GAP-34 | evidence_instance requires pre-existing case | HIGH |
| GAP-35 | case_access UNIQUE prevents permission level history | HIGH |
| GAP-36 | assertion.object_location_id is redundant | MEDIUM |
| GAP-37 | civix_user single role cannot represent multi-role | HIGH |
| GAP-38 | Neo4j CONTRADICTS edge self-contradictory | HIGH |
| GAP-39 | Expungement does not address free-text PII | HIGH |
| GAP-40 | Missing CCTV/media entity model | HIGH |
| GAP-41 | observer_type TEXT should be ENUM | MEDIUM |
| GAP-42 | source.agency_type TEXT should be ENUM | MEDIUM |
| GAP-43 | account_holder.holder_role TEXT should be ENUM | MEDIUM |
| GAP-44 | person.gender TEXT should be ENUM | LOW |
| GAP-45 | data_quality_issue.severity TEXT should be ENUM | MEDIUM |
| GAP-46 | legal_restriction.scope TEXT should be ENUM | MEDIUM |
| GAP-47 | legal_restriction.status TEXT should be ENUM | MEDIUM |
| GAP-48 | evidence_instance.legal_status TEXT should be ENUM | MEDIUM |
| GAP-49 | provenance table has no index strategy | MEDIUM |
| GAP-50 | Vehicle.entity_id in models.py means owner_id | MEDIUM |
| GAP-51 | Intelligence report classification field missing on source | MEDIUM |
| GAP-52 | Surveillance observer is Person not civix_user | MEDIUM |
| GAP-53 | SIM entity not modeled in generator world | MEDIUM |
| GAP-54 | ADR-021 referenced but does not exist | LOW |
| GAP-55 | test_world.py hard-codes absolute path | LOW |
| GAP-56 | case_entity_role lacks tx_start/tx_end | MEDIUM |
| GAP-57 | FIR table missing status field | MEDIUM |
| GAP-58 | case_link polymorphic FK not documented as ADR | MEDIUM |
| GAP-59 | SIM cardinality undefined | MEDIUM |
| GAP-60 | LOC-* location coordinates undefined | HIGH |
| GAP-61 | validator defaults disagree with config.py | HIGH |

---

## 6. Unresolved Conflicts Between Documents

### CONFLICT-01: Relationship Types in Neo4j vs ADR-007

**File A**: `13_NEO4J_GRAPH_BIBLE.md` — defines `[:CONTRADICTS]` as a named relationship type  
**File B**: ADR-007 in `CIVIX_CHANGE_CONTROL.md` — says CONTRADICT edges must NOT be topological  
**Conflict**: Having a named relationship type IS topological by Neo4j definition  
**Safer interpretation**: Use `[:HAS_STANCE]` with `stance` property  
**Proposed resolution**: Replace separate SUPPORTS/CONTRADICTS types with a single `[:HAS_STANCE]`  
**Human authorization required**: YES — affects Neo4j projection design

### CONFLICT-02: source_identity.extraction_id vs provenance

**File A**: `03_DATABASE_SCHEMA_BIBLE.md` — `source_identity.extraction_id FK→extraction`  
**File B**: ADR-006 — provenance linkages use application-enforced type+id, not direct FKs  
**Conflict**: extraction_id is a direct FK shortcut that contradicts the provenance design  
**Safer interpretation**: Remove extraction_id; use provenance table  
**Human authorization required**: YES — requires schema change

### CONFLICT-03: hypothesis_support bitemporal vs UNIQUE constraint

**File A**: `03_DATABASE_SCHEMA_BIBLE.md` — UNIQUE(hypothesis_id, assertion_id) on hypothesis_support  
**File B**: General architectural principle — audit trail for all investigative decisions  
**Conflict**: The UNIQUE constraint prevents historical tracking of stance changes  
**Safer interpretation**: Add bitemporal fields + loosen UNIQUE  
**Human authorization required**: YES — significant schema change

---

## 7. Open Decisions (Inherited from Previous Phases — Still Unresolved)

| Decision | Priority |
|---|---|
| Backend framework | HIGH |
| CDC consumer technology | HIGH |
| Acceptable Neo4j lag | HIGH |
| Clearance enforcement mechanism | MEDIUM |
| RLS for confidential informants | MEDIUM |
| Data retention periods | MEDIUM |
| ORM strategy | MEDIUM |
| ML model architecture | LOW |
| Frontend framework | LOW |

---

## 8. Architecture Decisions Required (New ADRs)

| ADR # | Topic | Priority |
|---|---|---|
| ADR-011 | case_link polymorphic relationship pattern | MEDIUM |
| ADR-012 | hypothesis_support bitemporal versioning | HIGH |
| ADR-013 | Neo4j HAS_STANCE relationship type (replaces SUPPORTS/CONTRADICTS) | HIGH |
| ADR-014 | evidence_instance case-first ingestion requirement | HIGH |
| ADR-015 | observer_entity_id vs observed_by for non-system observers | MEDIUM |
| ADR-016 | CCTV/media structured metadata approach | MEDIUM |
| ADR-017 | Expungement free-text PII handling | HIGH |
| ADR-018 | civix_user multi-role approach | HIGH |

---

## 9. Overall Verdict

**The architecture contains 7 CRITICAL gaps, 18 HIGH gaps, and 16 MEDIUM/LOW gaps.**

**CRITICAL gaps that MUST be resolved before DDL**:
1. 5 undefined ENUM types (hypothesis_status, lead_priority, lead_status, task_type, task_status)
2. Empty ground_truth.json
3. extraction_id on source_identity contradicts ADR-006
4. hypothesis_support UNIQUE constraint blocks audit trail
5. Neo4j CONTRADICTS relationship type is self-contradictory with ADR-007
6. Missing evidence classification field on source
7. LOC-* coordinates undefined (blocking ingestion design)

See `F_ARCHITECTURE_FREEZE_READINESS.md` for the final freeze verdict.
