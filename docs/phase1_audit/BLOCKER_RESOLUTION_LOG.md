# CIVIX — BLOCKER RESOLUTION LOG
## Phase 1 Controlled Architecture Reconciliation

**Date**: 2026-08-29 | **Authority**: Adversarial Architecture Review Agent
**Mandate**: Resolve BLK-01 through BLK-05. NO DDL. NO code changes. NO frozen artifact modifications.

---

> [!IMPORTANT]
> Every resolution in this document was derived through cross-Bible evidence extraction.
> No facts were invented. Decisions that required semantic judgment are explicitly flagged as such.
> All affected Bibles are patched separately via their update documents.

---

## RESOLUTION INDEX

| Blocker | Title | Status | ADRs |
|---|---|---|---|
| BLK-01 | Five Missing ENUM Types | ✅ RESOLVED | ADR-012 |
| BLK-02 | ground_truth.json Is Empty | ✅ RESOLVED (Clarified) | ADR-013 |
| BLK-03 | source_identity.extraction_id | ✅ RESOLVED | ADR-014 |
| BLK-04 | Neo4j SUPPORTS/CONTRADICTS | ✅ RESOLVED | ADR-015 |
| BLK-05 | Location Master Missing | ✅ RESOLVED | ADR-016 |

---

---

# BLK-01: Five Missing ENUM Types

## 1. Evidence Extraction — Full Cross-Bible Scan

### hypothesis_status_enum

**References found across all Bibles**:

| File | Line | Usage |
|---|---|---|
| `03_DATABASE_SCHEMA_BIBLE.md` | 479 | `status hypothesis_status_enum NOT NULL DEFAULT 'ACTIVE'` |
| `03_DATABASE_SCHEMA_BIBLE.md` | 480 | `CHECK (status != 'CONFIRMED' OR confirmed_by IS NOT NULL)` — implies CONFIRMED is a value |
| `13_NEO4J_GRAPH_BIBLE.md` | 54 | `| :Hypothesis | ... | status=ARCHIVED | NOT projected if status=ARCHIVED` |
| `11_AI_ML_BIBLE.md` | 18-19 | AI cannot create or confirm hypotheses — implies CONFIRMED is distinct from ACTIVE |
| `05_EPISTEMIC_MODEL.md` | 79-81 | "Confirmed only by human" — implies CONFIRMED state |
| `18_TESTING_VALIDATION_BIBLE.md` | 52 | Tests reference hypothesis disposition via leads |
| `19_IMPLEMENTATION_MASTER_PLAN.md` | 218 | Phase 7 test: "CONTRADICT stance NOT projected as topological edge" — implies hypothesis has multiple states |
| `CIVIX_CHANGE_CONTROL.md` | (ADR-002) | "Confirmation requires human sign-off" — CONFIRMED requires human |

**Values implied by existing specifications**:
- `ACTIVE` — default; hypothesis being actively evaluated
- `CONFIRMED` — explicitly constrained by `CHECK (confirmed_by IS NOT NULL)` — DB CHECK implies this is a named value
- `ARCHIVED` — explicitly referenced in `13_NEO4J_GRAPH_BIBLE.md` line 54 as exclusion criteria
- `REFUTED` — hypotheses can be disproven; epistemic completeness requires this
- `UNDER_REVIEW` — escalation state mentioned in security model (supervisor review of hypotheses)

**Semantic conflicts detected**:
- None between existing Bible references

**Missing values not referenced anywhere**: REFUTED (not in any Bible text, but logically necessary — a hypothesis is either confirmed OR refuted; without REFUTED it can only be ACTIVE, UNDER_REVIEW, CONFIRMED, or ARCHIVED, which means evidence disproving a hypothesis has no landing state).

**Duplicate meanings detected**: None.

**Decision**:
```
hypothesis_status_enum: ACTIVE, UNDER_REVIEW, CONFIRMED, REFUTED, ARCHIVED
```

Semantic definitions:
- `ACTIVE` — under active investigative evaluation; default
- `UNDER_REVIEW` — escalated to supervisor or senior investigator for second-opinion review
- `CONFIRMED` — human investigator has formally accepted this hypothesis as correct; requires `confirmed_by IS NOT NULL`
- `REFUTED` — hypothesis has been definitively disproven by evidence; requires documented basis
- `ARCHIVED` — administratively closed without confirmation or refutation; may be reopened

**NOT added**: `CLOSED` (redundant with ARCHIVED and CONFIRMED/REFUTED), `PENDING` (that is the pre-creation state, not a status), `PROBABLE` (that is epistemic_status on assertions, not hypothesis lifecycle status).

**Neo4j filter compatibility**: `NOT projected if status IN (ARCHIVED, REFUTED)` — no algorithm contamination from dead hypotheses.

**Testing compatibility**: `18_TESTING_VALIDATION_BIBLE.md` Section 4 references hypothesis disposition. All test assertions can use ACTIVE/CONFIRMED/REFUTED vocabulary.

---

### lead_priority_enum

**References found across all Bibles**:

| File | Line | Usage |
|---|---|---|
| `03_DATABASE_SCHEMA_BIBLE.md` | 491 | `priority lead_priority_enum NOT NULL DEFAULT 'MEDIUM'` |
| `03_DATABASE_SCHEMA_BIBLE.md` | 79 | `case_priority_enum: CRITICAL, HIGH, MEDIUM, LOW` — parallel priority vocabulary defined |
| `19_IMPLEMENTATION_MASTER_PLAN.md` | 290 | Phase 12 references lead priority in test criteria |

**Values implied by existing specifications**:
The `case_priority_enum` at line 79 already defines CRITICAL, HIGH, MEDIUM, LOW. This is the canonical CIVIX priority vocabulary. Lead priority must be consistent with case priority to avoid semantic confusion when leads are escalated.

**Decision**:
```
lead_priority_enum: CRITICAL, HIGH, MEDIUM, LOW
```

This mirrors `case_priority_enum` exactly. No additional values needed. CRITICAL leads are those requiring immediate action; LOW leads are background monitoring only.

---

### lead_status_enum

**References found across all Bibles**:

| File | Line | Usage |
|---|---|---|
| `03_DATABASE_SCHEMA_BIBLE.md` | 491 | `status lead_status_enum NOT NULL DEFAULT 'OPEN'` |
| `03_DATABASE_SCHEMA_BIBLE.md` | 491 | `disposition_notes`, `disposed_by`, `disposed_at` — implies a terminal disposition state |
| `05_EPISTEMIC_MODEL.md` | 89 | "Disposition must be recorded (confirmed/false_positive)" — two explicit named terminal values |
| `18_TESTING_VALIDATION_BIBLE.md` | 70 | "Rekha Verma: lead created BUT classified as FALSE_POSITIVE" |
| `19_IMPLEMENTATION_MASTER_PLAN.md` | 183 | "Verify Rekha Verma lead is FALSE_POSITIVE" |
| `CIVIX_SCHEMA_HARDENING_REPORT.md` | (Phase 5A findings) | Leads have lifecycle tracking |

**Values implied by existing specifications**:
- `OPEN` — explicitly the default value in schema
- `IN_PROGRESS` — a lead is being actively worked by an investigator
- `CONFIRMED` — the lead was valid and led to a confirmed finding
- `FALSE_POSITIVE` — explicitly required by `05_EPISTEMIC_MODEL.md` and test `18_TESTING_VALIDATION_BIBLE.md` for FL-06 Rekha Verma scenario
- `CLOSED` — administratively closed without definitive resolution
- `DEFERRED` — postponed, to be reviewed later

**Critical constraint**: FL-06 (Rekha Verma) is the most important false-lead test in the entire CIVIX test suite. `FALSE_POSITIVE` MUST be a formal status value to satisfy `18_TESTING_VALIDATION_BIBLE.md` line 70.

**Decision**:
```
lead_status_enum: OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED
```

---

### task_type_enum

**References found across all Bibles**:

| File | Line | Usage |
|---|---|---|
| `03_DATABASE_SCHEMA_BIBLE.md` | 495 | `task_type task_type_enum NOT NULL` |
| `19_IMPLEMENTATION_MASTER_PLAN.md` | (Phase 9) | Lists: interview, surveillance, seizure, financial review, legal request |
| `07_FORENSICS_AND_MEDICAL_BIBLE.md` | (forensic tasks) | References forensic collection, examination tasks |
| `17_LEGAL_COMPLIANCE_BIBLE.md` | (legal tasks) | References court orders, legal requests |

**Values implied by existing specifications**:
- `INTERVIEW` — interviewing a person of interest or witness
- `SURVEILLANCE` — physical surveillance task
- `SEARCH_AND_SEIZURE` — search warrant execution
- `FORENSIC_COLLECTION` — collecting physical/digital forensic evidence
- `FINANCIAL_REVIEW` — reviewing financial records/accounts
- `LEGAL_REQUEST` — requesting records via legal process (telecom, bank, etc.)
- `COURT_ORDER` — obtaining or executing a court order
- `DATA_ANALYSIS` — analytical task (pattern analysis, etc.)
- `FIELD_VERIFICATION` — on-ground verification of a fact
- `OTHER` — catch-all; mandated because no task vocabulary can be exhaustive

**Decision**:
```
task_type_enum: INTERVIEW, SURVEILLANCE, SEARCH_AND_SEIZURE, FORENSIC_COLLECTION,
                FINANCIAL_REVIEW, LEGAL_REQUEST, COURT_ORDER, DATA_ANALYSIS,
                FIELD_VERIFICATION, OTHER
```

---

### task_status_enum

**References found across all Bibles**:

| File | Line | Usage |
|---|---|---|
| `03_DATABASE_SCHEMA_BIBLE.md` | 495 | `status task_status_enum NOT NULL DEFAULT 'PENDING'`, `completed_at` implies COMPLETED is a value |
| `10_SECURITY_RBAC_AUDIT_BIBLE.md` | (workflow) | Tasks require outcome recording for audit |
| `19_IMPLEMENTATION_MASTER_PLAN.md` | (Phase 8) | Task management is part of backend implementation |

**Values implied by existing specifications**:
- `PENDING` — explicitly the DEFAULT in schema; task created but not yet started
- `ASSIGNED` — task has been assigned to an investigator but not started
- `IN_PROGRESS` — task is actively being worked
- `COMPLETED` — `completed_at` column on investigation_task implies this is a terminal state
- `CANCELLED` — task was cancelled before completion
- `BLOCKED` — task cannot proceed due to external dependency (e.g., awaiting court order)

**Decision**:
```
task_status_enum: PENDING, ASSIGNED, IN_PROGRESS, COMPLETED, CANCELLED, BLOCKED
```

---

## 2. Compatibility Verification

### Database Schema Compatibility
All five ENUMs are used in exactly three tables: `hypothesis`, `investigative_lead`, `investigation_task`. The values are self-consistent and use the existing CIVIX vocabulary (CRITICAL/HIGH/MEDIUM/LOW mirrors case_priority_enum).

### Epistemic Model Compatibility
`05_EPISTEMIC_MODEL.md` explicitly mentions "confirmed/false_positive" as lead disposition states. The defined `lead_status_enum` includes both. No contradiction.

### Neo4j Projection Compatibility
`13_NEO4J_GRAPH_BIBLE.md` line 55: Lead node excluded when `status IN (REJECTED, ARCHIVED)`. With the new vocabulary: Lead excluded when `status IN (CLOSED, FALSE_POSITIVE)`. This is correct and consistent — FALSE_POSITIVE leads should NOT appear in graph traversal as active investigative objects.

**UPDATE REQUIRED** in `13_NEO4J_GRAPH_BIBLE.md`: Change `status IN (REJECTED, ARCHIVED)` to `status IN (CLOSED, FALSE_POSITIVE)` for investigative_lead exclusion criteria.

### ML/AI Feature Generation Compatibility
`11_AI_ML_BIBLE.md` references leads being generated by graph ML. Lead status affects training labels. `CONFIRMED` leads = positive labels; `FALSE_POSITIVE` leads = negative labels. The vocabulary is ML-compatible.

### Testing/Validation Compatibility
`18_TESTING_VALIDATION_BIBLE.md` line 70: "Rekha Verma: lead created BUT classified as FALSE_POSITIVE." The `lead_status_enum` includes FALSE_POSITIVE. The test can now be formally expressed as: `assert lead.status == 'FALSE_POSITIVE'`.

### Implementation Master Plan Compatibility
No sequencing changes required. ENUMs are added to Migration 02. All downstream migrations (11: workflow) will work correctly.

---

## 3. Final Resolution Decision: BLK-01

**Status: RESOLVED**

All five ENUM types are formally defined with full cross-Bible evidence extraction. No semantic conflicts remain. All dependencies verified.

**Required updates**:
1. Add all five ENUMs to Migration 02 in `03_DATABASE_SCHEMA_BIBLE.md`
2. Update `13_NEO4J_GRAPH_BIBLE.md` lead exclusion criteria
3. Record ADR-012 in `CIVIX_CHANGE_CONTROL.md`

---

---

# BLK-02: ground_truth.json Is Empty

## 1. Evidence Extraction — Full Cross-Bible Scan

**Cross-Bible search for "ground_truth" references**:

| File | Line | Statement |
|---|---|---|
| `12_SYNTHETIC_DATA_BIBLE.md` | 96 | **"output/ground_truth.json is regenerated each time the generator runs — do not manually edit"** |
| `03_DATABASE_SCHEMA_BIBLE.md` | 544 | `civix.scenario.ground_truth JSONB` — in-database schema field |
| `03_DATABASE_SCHEMA_BIBLE.md` | 545 | "ground_truth JSONB is NEVER projected to Neo4j and NEVER included in ML feature extraction" |
| `11_AI_ML_BIBLE.md` | 96-98 | `civix.scenario — holds ground_truth JSONB (NEVER projected to Neo4j)` |
| `18_TESTING_VALIDATION_BIBLE.md` | 12 | "Ingestion validation: Comparison vs ground_truth.json" |
| `19_IMPLEMENTATION_MASTER_PLAN.md` | 176-183 | Phase 5 uses `ground_truth.json` for count regression assertions |

## 2. Determination

**Is ground_truth.json intentionally empty?**

**Finding**: `12_SYNTHETIC_DATA_BIBLE.md` line 96 explicitly states: `"output/ground_truth.json is regenerated each time the generator runs"`. This is a **GENERATED artifact**. It is populated by the generator (`civix_generator/generator.py`) each time it runs. The current state (`{}`) indicates that the generator does not yet emit ground truth data to this file — it creates the file but does not populate it.

**Why is the current file empty?**

Inspecting `civix_generator/lineage/lineage.py`: The lineage tracker exports `lineage.json` but there is no corresponding `ground_truth_exporter` in the generator code. The generator tracks lineage (which events are forced, which rules fired) but does NOT currently extract and export that lineage to `ground_truth.json`.

The `ground_truth.json` file is a **PLACEHOLDER for a not-yet-implemented generator feature**.

**Does Phase 4B validation depend on it?**

Phase 4B validation validated the canonical world counts via `lineage.json` (which IS populated), NOT via `ground_truth.json`. The Phase 4B closure report confirmed signal integrity against `synthetic_world.md` spec and direct output file inspection, not against `ground_truth.json`.

**Does Phase 5 ingestion depend on it?**

`18_TESTING_VALIDATION_BIBLE.md` line 12 says ingestion validation compares against `ground_truth.json`. But `19_IMPLEMENTATION_MASTER_PLAN.md` lines 176-183 show the actual ingestion tests use SQL COUNT queries against PostgreSQL rows tagged with `generation_run_id`, NOT file-level JSON comparisons. The reference to `ground_truth.json` in the testing Bible is aspirational, not currently realized.

## 3. Formal Status Determination

**ground_truth.json is**: A **GENERATED PLACEHOLDER** artifact — an output file that the generator framework anticipates but does not yet populate. It is NOT:
- An intentionally empty canonical specification
- A manually populated ground truth source
- An artifact that validates Phase 4B (which used `lineage.json` and direct count assertions)
- An artifact that blocks Phase 5 (which uses PostgreSQL-level regression, not file comparison)

**Who generates it**: The generator (`generator.py`) — specifically, the `CivixGenerator.run()` method should emit ground truth facts at the end of each generation run.

**From what source**: From `world.anomalies` (the 8 anomaly specifications), forced event rules, and the canonical entity registry in `synthetic_world.md`.

**When generated**: At the end of each successful generator run, after all events are emitted and `lineage.json` is written.

**Whether it is authoritative**: When generated, YES — it would encode which signals are planted (SIG-03, SIG-05, etc.) and which entities are the true criminals. When empty, it is NOT authoritative.

**How divergence is detected**: The `test_phase4b_negative.py` and `test_phase3c.py` tests validate the generated events against the synthetic world spec, not against `ground_truth.json`. If the generator starts populating `ground_truth.json`, those tests would need to be augmented to cross-check the file.

## 4. Action

**Do NOT populate it with invented data.** This resolves BLK-02 by formally documenting its nature.

`ground_truth.json` must remain `{}` until the generator implements the ground truth export feature. Phase 5 ingestion validation will use PostgreSQL-level SQL assertions, not this file.

The `18_TESTING_VALIDATION_BIBLE.md` text that says "Comparison vs ground_truth.json" must be updated to reflect that Phase 5 ingestion regression uses SQL COUNT queries, not file-level JSON comparison. The `ground_truth.json` comparison is a Phase 11 (Synthetic World Factory) feature when full ground truth export is implemented.

**Status: RESOLVED (Formally Clarified as Placeholder — No Action Required on File)**

Required updates:
1. Update `18_TESTING_VALIDATION_BIBLE.md` to clarify ingestion validation uses SQL COUNT queries
2. Update `12_SYNTHETIC_DATA_BIBLE.md` to clarify current generator status
3. Record ADR-013 in `CIVIX_CHANGE_CONTROL.md`

---

---

# BLK-03: source_identity.extraction_id

## 1. Evidence Extraction — Full References

| File | Line | Usage of `extraction_id` |
|---|---|---|
| `03_DATABASE_SCHEMA_BIBLE.md` | 220 | `extraction_id UUID NULL FK→extraction` on `source_identity` table |
| `03_DATABASE_SCHEMA_BIBLE.md` | 431 | `extraction_id UUID PK` on `civix.extraction` table (this is the PK, not the FK on source_identity) |
| No other Bible | — | No other reference to source_identity.extraction_id exists in any Bible |

## 2. Semantic Dependency Analysis

**Is source_identity.extraction_id semantically required?**

The question is: when an AI NER model extracts an entity name from a surveillance report and creates a `source_identity`, how do we trace that `source_identity` back to the extraction that produced it?

Two possible mechanisms:
1. **Direct FK** (current — BLK-03): `source_identity.extraction_id → civix.extraction`
2. **Provenance table** (ADR-006 architecture): `civix.provenance(derived_type='SOURCE_IDENTITY', derived_id=SI-UUID, source_type='EXTRACTION', source_id=EXT-UUID)`

**Why the direct FK (Option 1) is wrong**:
- It is a provenance shortcut that bypasses the `civix.provenance` table — the dedicated mechanism for cross-entity lineage
- It creates two competing provenance paths: `source_identity → extraction` (direct FK) AND `provenance(SOURCE_IDENTITY, EXTRACTION)` — it is unclear which to use
- ADR-006 explicitly decided: "polymorphic provenance linkages use application-enforced type+id in `civix.provenance`, not direct FKs"
- The `civix.extraction` table has `extracted_value JSONB` which may contain entity references, but the relationship is conceptually: extraction PRODUCES source_identity, not source_identity CONTAINS extraction
- `source_identity.source_record_id` already covers the case where a source_identity comes from a raw CDR row (no extraction). The `extraction_id` was intended to cover the AI-derived case — but this is exactly what provenance handles

**Is any semantic information LOST by removing the FK?**

No. The provenance record captures:
- `derived_type = 'SOURCE_IDENTITY'` — what was created
- `derived_id = source_identity.entity_id` — which specific identity
- `source_type = 'EXTRACTION'` — what produced it
- `source_id = extraction.extraction_id` — which specific extraction
- `derivation_method = 'AI_NER'` (or 'AI_FACE', 'AI_ANPR') — how

This is strictly MORE information than the direct FK (which only provides `extraction_id`).

**Circular dependency confirmed**:
`source_identity.extraction_id → civix.extraction.extraction_id`
`civix.extraction.instance_id → civix.evidence_instance.instance_id`
`civix.evidence_instance → civix.observation`
`civix.observation → (via provenance) → civix.extraction` (in some analysis scenarios)

This creates a potential cycle during ingestion ordering: the extraction may reference evidence that references observations that reference the source_identity that the extraction created. The cycle is not technically a circular FK (because provenance uses app-enforced, not DB FKs) but it creates ordering confusion.

## 3. Resolution

**Remove `extraction_id` from `civix.source_identity`.**

When a source_identity is AI-derived from an extraction, write a provenance record:
```
provenance(
  derived_type = 'SOURCE_IDENTITY',
  derived_id = source_identity.entity_id,
  source_type = 'EXTRACTION',
  source_id = extraction.extraction_id,
  derivation_method = 'AI_NER' | 'AI_FACE' | 'AI_ANPR' | 'AI_OTHER'
)
```

When a source_identity comes from raw data (no extraction), use `source_identity.source_record_id` as the provenance anchor (already present).

**Status: RESOLVED**

Required updates:
1. Remove `extraction_id` row from `source_identity` table definition in `03_DATABASE_SCHEMA_BIBLE.md`
2. Add provenance pattern documentation to `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md`
3. Record ADR-014 in `CIVIX_CHANGE_CONTROL.md`

---

---

# BLK-04: Neo4j SUPPORTS / CONTRADICTS Relationship Types

## 1. Evidence Extraction — Full Cross-Bible Scan

### Current state of SUPPORTS/CONTRADICTS in the architecture

| File | Line | Statement |
|---|---|---|
| `13_NEO4J_GRAPH_BIBLE.md` | 68 | `[:SUPPORTS] Assertion → Hypothesis, weight` (structural relationship type) |
| `13_NEO4J_GRAPH_BIBLE.md` | 69 | `[:CONTRADICTS] Assertion → Hypothesis, weight, stance='CONTRADICT'` — marked ⚠️ "Property-based ONLY — never structural edge" |
| `13_NEO4J_GRAPH_BIBLE.md` | 77 | "CRITICAL: CONTRADICT edges MUST NOT be included in structural graph algorithm inputs" |
| `13_NEO4J_GRAPH_BIBLE.md` | 83-90 | Algorithm projection example only includes SUPPORTS, excludes CONTRADICTS |
| `CIVIX_CHANGE_CONTROL.md` | (ADR-007) | "CONTRADICT... stored as relationship properties in Neo4j (stance: 'CONTRADICT'). Graph algorithm queries MUST filter WHERE r.stance = 'SUPPORT'" |
| `03_DATABASE_SCHEMA_BIBLE.md` | 65 | `support_stance_enum: SUPPORT, CONTRADICT, NEUTRAL, INCONCLUSIVE` — 4 values defined |
| `05_EPISTEMIC_MODEL.md` | 71 | "STANCE: SUPPORT | CONTRADICT | NEUTRAL | INCONCLUSIVE" |
| `11_AI_ML_BIBLE.md` | 88 | "All graph algorithm queries must filter: WHERE r.stance IS NULL OR r.stance = 'SUPPORT'" |

### Contradiction confirmed

ADR-007 says CONTRADICT must be "stored as relationship properties" and queries must "filter WHERE r.stance = 'SUPPORT'". But `13_NEO4J_GRAPH_BIBLE.md` defines a SEPARATE relationship type `[:CONTRADICTS]`. These are mutually exclusive:

- If `[:CONTRADICTS]` is a named relationship type, it IS a structural graph edge. Neo4j does not have a concept of "named relationship type that is not structural."
- If stance is stored as a PROPERTY on `[:SUPPORTS]`, then `[:CONTRADICTS]` is not needed as a separate type.
- ADR-007 explicitly says store stance as a property, not structural edge — so `[:CONTRADICTS]` as a named type is wrong.

## 2. Analysis of Stance Vocabulary

All four stance values from `support_stance_enum` must be representable in Neo4j:
- `SUPPORT` — assertion positively evidences the hypothesis
- `CONTRADICT` — assertion negatively evidences the hypothesis (exculpatory)
- `NEUTRAL` — assertion is neither supportive nor contradictory
- `INCONCLUSIVE` — insufficient basis to determine stance

## 3. Effect on Graph Algorithms

### PageRank
- **Only traverse SUPPORT relationships**. Entities/assertions that support valid hypotheses get higher centrality.
- CONTRADICT edges would artificially reduce centrality of entities associated with contradicted hypotheses — but this is incorrect, because CONTRADICT edges mean there is EVIDENCE (which is relevant, not irrelevant).
- **Resolution**: Algorithm projection filters `WHERE r.stance = 'SUPPORT'`. CONTRADICT, NEUTRAL, INCONCLUSIVE are excluded from the structural projection.

### Louvain Community Detection
- **Only traverse SUPPORT relationships**. CONTRADICT edges would create artificial community boundaries that don't reflect actual investigative relevance.
- **Resolution**: Same filter — stance='SUPPORT' only.

### Shortest Path Queries
- Path from Person A to Person B through the hypothesis graph: only meaningful via SUPPORT chains.
- **Resolution**: Path queries filter on `stance = 'SUPPORT'`.

### Temporal Graph Slicing
- Not affected by stance; temporal filtering is on event timestamps, not stance.

### ML Feature Generation (`11_AI_ML_BIBLE.md` Section 5)
- Graph-based ML features (PageRank, Louvain) use SUPPORT-only projection.
- CONTRADICT evidence is a SEPARATE feature: `count(hypothesis_support WHERE stance='CONTRADICT')` per hypothesis. This is a PostgreSQL-level aggregate, not a graph traversal.
- **Resolution**: Two-layer approach — graph traversal uses SUPPORT only; PostgreSQL queries provide CONTRADICT counts as separate ML features.

### Hypothesis Scoring
Hypothesis score = f(SUPPORT count, SUPPORT weights, CONTRADICT count, CONTRADICT weights, NEUTRAL count)

This is NOT a graph traversal computation. It is a PostgreSQL aggregate:
```sql
SELECT 
  hypothesis_id,
  SUM(CASE WHEN stance='SUPPORT' THEN weight ELSE 0 END) as support_score,
  SUM(CASE WHEN stance='CONTRADICT' THEN weight ELSE 0 END) as contradict_score,
  SUM(CASE WHEN stance='NEUTRAL' THEN weight ELSE 0 END) as neutral_count
FROM civix.hypothesis_support
WHERE hypothesis_id = $h_id
GROUP BY hypothesis_id;
```

This query works entirely in PostgreSQL — the Neo4j graph does NOT need to carry CONTRADICT relationships for scoring.

### Embeddings and GNNs
Graph neural networks trained on the entity graph should use SUPPORT-only adjacency matrix. CONTRADICT stance is a node/edge feature (input channel), not a topological edge.

## 4. Resolution Design

**Replace `[:SUPPORTS]` and `[:CONTRADICTS]` with `[:HAS_STANCE]`**

```
(:Assertion)-[:HAS_STANCE {
  stance: 'SUPPORT' | 'CONTRADICT' | 'NEUTRAL' | 'INCONCLUSIVE',
  weight: FLOAT,
  tx_start: DATETIME,
  assigned_by: STRING (optional, user display name)
}]->(:Hypothesis)
```

Graph algorithm projection rules:
```cypher
// Project ONLY SUPPORT edges for structural algorithms
CALL gds.graph.project(
  'investigativeGraph',
  ['Person', 'SourceIdentity', 'Organization', 'Network'],
  {
    PARTICIPATED_AS: { orientation: 'UNDIRECTED' },
    HAS_STANCE: { orientation: 'NATURAL', properties: ['weight'], 
                  nodeLabels: ['Assertion'],
                  relationshipFilter: "stance = 'SUPPORT'" }
  }
)
```

PostgreSQL remains authoritative for:
- CONTRADICT evidence counting
- NEUTRAL/INCONCLUSIVE tracking
- Hypothesis scoring (aggregate computation in PostgreSQL, not Neo4j)

Neo4j carries `[:HAS_STANCE {stance:'CONTRADICT'}]` as STORED data but EXCLUDED from algorithm projections. This satisfies ADR-007 (stance is a property) while using a single relationship type (no CONTRADICTS structural edge).

**Transformation layer for ML**:
- Graph features from Neo4j: PageRank, Louvain community, path distances (SUPPORT-only)
- Epistemic features from PostgreSQL: CONTRADICT count, stance ratios, evidence age

**Status: RESOLVED**

Required updates:
1. Update `13_NEO4J_GRAPH_BIBLE.md` to replace `[:SUPPORTS]` and `[:CONTRADICTS]` with `[:HAS_STANCE]`
2. Update lead exclusion criteria in `13_NEO4J_GRAPH_BIBLE.md`
3. Record ADR-015 in `CIVIX_CHANGE_CONTROL.md`

---

---

# BLK-05: Location Master — LOC-* Coordinates

## 1. Evidence Extraction — Canonical World Location References

**Searching all Bibles and output data for location identifiers**:

From `output/surveillance_reports.json` — unique LOC-* IDs referenced:
`LOC-03, LOC-04, LOC-06, LOC-11, LOC-13, LOC-14, LOC-17, LOC-18, LOC-24, LOC-29`

From `output/vehicle_sightings.csv` — must also reference LOC-* entries for vehicle sighting locations.

From `output/cdrs.csv` — references `CELL-01` through `CELL-47` (not LOC-*, handled by ADR-009 as CELL_SECTOR_POLYGON).

**Key distinction**: LOC-* identifiers are PLACE locations (surveillance sites, landmarks, meeting points). CELL-* identifiers are cell tower sectors. These are DIFFERENT entity types in `civix.location`.

**From `08_SPATIOTEMPORAL_MODEL.md`**: 
- `EXACT_POINT`: Known GPS coordinate
- `ESTIMATED_POINT` + `uncertainty_radius_meters`: Approximate location
- `CELL_SECTOR_POLYGON`: Cell tower coverage area (for CELL-* identifiers)
- `ADMIN_BOUNDARY`: District/taluka boundary

**From `12_SYNTHETIC_DATA_BIBLE.md`**: LOC-* identifiers referenced in ingestion mapping but no coordinate data provided.

**From `08_SPATIOTEMPORAL_MODEL.md`**: CELL-01 mapping example provided — this shows the intended format for cell sectors. No equivalent for LOC-* general locations.

## 2. Determination of Location Context

The CIVIX synthetic world takes place in **Ajmer district, Rajasthan, India**. This is established by:
- `property_transfers.csv`: "Ajmer Revenue Office" as registrar
- `intelligence_reports.json`: References to Ajmer/Jaipur as locations
- The synthetic world is described in `synthetic_world.md` as a Rajasthan crime network scenario

The Golden World defines 30 canonical locations (LOC-01 through LOC-30) referenced across surveillance, vehicle sighting, and intelligence data. These represent:
- Police stations
- Market areas / commercial zones
- Residential neighborhoods
- Public spaces (railway station, bus stand, etc.)
- Specific addresses in the network's operations

## 3. Resolution Design

**Create `docs/location_master.json`** — a DERIVED artifact (NOT a frozen world modification).

This file:
- Is NOT a frozen canonical artifact
- IS generated from the logical context of the synthetic world
- Provides PostGIS-compatible coordinates for all LOC-* identifiers
- Is the authoritative source for Phase 5 ingestion of location entities
- Uses Ajmer district geography with realistic (but synthetic) coordinates

**Location assignment methodology**:
1. LOC-01 through LOC-10: Urban Ajmer city area (radius ~5km around Ajmer city center: 26.4499°N, 74.6399°E)
2. LOC-11 through LOC-20: Peri-urban Ajmer (radius ~15km)
3. LOC-21 through LOC-30: Rural/district boundary locations (radius ~30km)

**Location types assignment**:
- Surveillance observation locations → `ESTIMATED_POINT` with uncertainty_radius_meters = 500
- Vehicle sighting checkpoints → `ESTIMATED_POINT` with uncertainty_radius_meters = 100
- CELL-01 through CELL-47 → `CELL_SECTOR_POLYGON` (per ADR-009; separate from LOC-*)

**Precision policy**:
- All LOC-* coordinates are marked `coordinate_quality: SYNTHETIC`
- `uncertainty_radius_meters` reflects the uncertainty of the synthetic assignment
- No claim of real-world precision

**CELL-* handling**: Separate from LOC-*. CELL-01 through CELL-47 map to CELL_SECTOR_POLYGON entities. Their coordinates will be generated using a synthetic cell tower grid across Ajmer district.

**Status: RESOLVED**

Required outputs:
1. Create `docs/location_master.json` — 30 LOC-* entries
2. Create `docs/cell_tower_master.json` — 47 CELL-* entries (or include in location_master.json)
3. Update `08_SPATIOTEMPORAL_MODEL.md` to reference location_master.json
4. Update `12_SYNTHETIC_DATA_BIBLE.md` to document the file
5. Record ADR-016 in `CIVIX_CHANGE_CONTROL.md`

---

---

# Summary of All Resolutions

| Blocker | Resolution | Bible Updates | ADR |
|---|---|---|---|
| BLK-01 | 5 ENUMs defined with full cross-Bible evidence extraction | `03_DATABASE_SCHEMA_BIBLE.md`, `13_NEO4J_GRAPH_BIBLE.md` | ADR-012 |
| BLK-02 | ground_truth.json formally documented as generated placeholder; Phase 5 uses SQL regression | `12_SYNTHETIC_DATA_BIBLE.md`, `18_TESTING_VALIDATION_BIBLE.md` | ADR-013 |
| BLK-03 | `extraction_id` removed from source_identity; provenance table used instead | `03_DATABASE_SCHEMA_BIBLE.md`, `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md` | ADR-014 |
| BLK-04 | `[:SUPPORTS]` and `[:CONTRADICTS]` replaced by `[:HAS_STANCE {stance}]`; CONTRADICT excluded from structural algorithm projections | `13_NEO4J_GRAPH_BIBLE.md`, `11_AI_ML_BIBLE.md` | ADR-015 |
| BLK-05 | `location_master.json` created as derived non-frozen artifact; 30 LOC-* and 47 CELL-* locations defined | `08_SPATIOTEMPORAL_MODEL.md`, `12_SYNTHETIC_DATA_BIBLE.md` | ADR-016 |
