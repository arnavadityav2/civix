# C4 Blocker Root-Cause Investigation

## 1. Executive Conclusion
The C4 deterministic engine and pipeline logic are functioning correctly. Both remaining blockers are caused by data ingestion and extraction flaws in the C0/C2 layers, NOT by failures in the C3/C4 investigative logic or Neo4j projection. 

- **Blocker 1 (Vikram ↔ Neha):** Fails due to a **Fixture/Data Construction Defect**. The intermediate node ("Neha Coordinator") was ingested directly as a `PERSON` entity rather than a `source_identity`, circumventing the identity resolution engine entirely.
- **Blocker 2 (Vikram ↔ Global Exports):** Fails due to an **Extraction/Mapping Defect**. The raw evidence contains the relationship, but the extraction pipeline failed to parse it into a structured assertion in the database.

The C4 **CONDITIONAL** status should remain unchanged until these upstream data issues are resolved.

---

## 2. Blocker 1 — Vikram ↔ Neha

### Complete Evidence Chain
1. **Assertion:** `fb123ba2-737a-4d12-ad72-93a3bf9efcd3 (Vikram)` --[KNOWN_ASSOCIATE_OF]--> `f0c5c064-7955-4d5c-b327-78d33889905d (Neha Coordinator)`.
2. **Entity Analysis:** The ID `f0c5c064-7955-4d5c-b327-78d33889905d` belongs to a `PERSON` entity (Display Name: "Neha Coordinator"), created at `2026-09-01 18:16:39 UTC`.
3. **Identity Resolution:** There are **0** `identity_candidate` records and **0** `identity_resolution` records linking `f0c5c064...` to the true Neha Gupta entity (`14fb86ef...`).

### Exact Path Attempt & Failure Reason
- **Why it fails:** The path traverses `Vikram -> Neha Coordinator`, but stops there. 
- **Root Cause:** The C0 Golden World data generation scripts injected "Neha Coordinator" directly into the `civix.person` table instead of the `civix.source_identity` table. The C2 identity resolution engine operates strictly by scoring and merging `source_identity` records into `person` records. Because "Neha Coordinator" was already a `person`, it bypassed the resolution engine entirely, leaving the graph disconnected.

### Classification
**Fixture/Data Construction Defect.** The deterministic rules could not fire because the data was inserted at the wrong abstraction layer.

---

## 3. Blocker 2 — Vikram ↔ Global Exports

### Ground-Truth vs Evidence Comparison
- **Ground Truth Matrix:** Asserts `Vikram ↔ Global Exports Pvt Ltd`.
- **Database Raw Evidence:** 12 separate `civix.observation` records contain the exact text combining both entities (e.g., `"Vikram Singh is reportedly an associate of Global Exports Pvt Ltd."`).
- **Database Assertions:** There are **0** assertions in the `civix.assertion` table linking Vikram to *any* organization.
- **Neo4j:** No relationship exists.

### Complete Evidence Chain Failure
1. **Evidence Instance / Observation:** Successfully captured the text containing both entities.
2. **Extraction:** The structured LLM extraction failed to map the text into an assertion payload.
3. **Assertion / Projection:** Because the extraction step returned nothing, no `assertion` was created, and Neo4j received no edge.

### Classification
**Extraction/Mapping Defect.** The source evidence is perfectly consistent with the ground-truth matrix, but the C2 information extraction pipeline dropped the relationship. This could be due to a strict ontology schema rejecting `ASSOCIATE_OF` between a `PERSON` and an `ORGANIZATION`, or an LLM parsing failure.

---

## 4. Minimal Remediation Options (Not Implemented)

> [!IMPORTANT]
> **No changes have been made to the database, source code, or Golden World fixtures.**

**For Blocker 1:**
- *Option A:* Modify the C0 Golden World ingestion scripts to ensure all discovered aliases/coordinators are ingested as `source_identity` records with appropriate `raw_name` and `attributes` payloads, allowing the C2 engine to legitimately score and merge them.
- *Option B:* If manual resolution is allowed under the C2 rules, simulate an investigator creating an explicit `SAME_AS` edge or `identity_merge_event` between the two `PERSON` entities.

**For Blocker 2:**
- *Option A:* Review the LLM extraction prompt and ontology in C2. Ensure the schema permits relationships (like `AFFILIATED_WITH` or `EMPLOYED_BY`) between `PERSON` and `ORGANIZATION` when parsing texts like "is reportedly an associate of".
- *Option B:* Modify the `generate_synthetic_docs.py` to use stronger, more explicit phrasing (e.g., "Vikram Singh is employed by Global Exports") if the extractor requires stricter verbs.

## 5. Recommendation for Next Authorized Step
I recommend maintaining the **CONDITIONAL** status of C4. 

The user must authorize whether to:
1. Re-open C0/C2 to fix the data ingestion/extraction bugs, reset the database, and re-run the pipeline.
2. Or, accept the CONDITIONAL state as sufficient proof of the C4 engine's logic (since it correctly rejected unproven paths) and explicitly authorize the commencement of C5.

**FROZEN ASSETS:** The Golden World artifacts, `ground_truth.json`, and all current PostgreSQL/Neo4j database states remain strictly frozen as mandated.
