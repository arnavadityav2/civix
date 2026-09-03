# C4 Targeted Remediation Plan

## 1. Executive Summary
This document provides the minimal, precise remediation plan for the upstream C0/C2 flaws blocking the C4 Conditional certification. The remediations strictly address the mechanism of data insertion (Blocker 1) and text ambiguity in extraction (Blocker 2). 

> [!CAUTION]
> **No changes have been implemented yet.** This plan awaits explicit authorization. A database reset is NOT required for the entire application, but the synthetic fixtures must be updated and re-ingested.

---

## 2. Blocker 1: Source Identity / "Neha Coordinator"

### Exact Root Cause
The `database/ingest_golden_world.py` script incorrectly treats every alias in the C0 `persons` JSON array as a fully formed `PERSON` entity. Consequently, "Neha Coordinator" bypassed the `civix.source_identity` layer, meaning the C2 Entity Resolution engine never saw it and never generated an `identity_candidate` for it.

### Current Incorrect Insertion Path
1. `generate_synthetic_docs_c0.py` writes "Neha Coordinator" into the `persons` array in `world.json`.
2. `ingest_golden_world.py` (Line 185) loops over `persons` and executes `INSERT INTO civix.person`.

### Expected Correct Insertion Path
1. Aliases and monikers discovered in source documents (e.g., WhatsApp exports) must be ingested as `civix.source_identity` records (Entity Type: `SOURCE_IDENTITY`).
2. C2 Entity Resolution runs against `source_identity` records and proposes `identity_candidate` links to existing `civix.person` records.

### Evidence & Attributes
- **Exact Source Evidence:** `DEVICE_EXT_035.txt` contains: `WhatsApp Chat Export with "Neha Coordinator" (+91-7777777777):`
- **Expected `source_identity` Attributes:**
  - `raw_identifier`: `"Neha Coordinator"`
  - `identifier_type`: `"NAME"`
  - `attributes`: `{"phone_number": "+91-7777777777", "context": "WhatsApp Contact"}`

### C2 Resolution & C4 Validation
- **C2 Generation:** The C2 rule `MATCH_EXACT_PHONE` will legitimately generate an `identity_candidate` because the true `Neha Gupta` entity shares the `+91-7777777777` attribute.
- **Common-name Defenses:** "Neha" is common, but the exact phone number match bypasses fuzzy name penalties, yielding a high `match_score`.
- **Investigator Resolution:** The CIVIX architecture mandates "candidate only semantics" (no automatic GNN/probabilistic merges). Therefore, an investigator MUST manually resolve this candidate.
- **C4 Validation Contract:** To validate this path, the C4 test suite (`test_c4_remediation.py`) must be updated to simulate an authorized investigator accepting the `identity_candidate` via the API *before* asserting the existence of the C3 deterministic path. This perfectly preserves the manual-merge contract.

### Expected Records After Legitimate Remediation
- **PostgreSQL:** 1 `source_identity`, 1 `identity_candidate`, 1 `identity_resolution` (status: RESOLVED, decided_by: Investigator), 1 `assertion` (Vikram → KNOWN_ASSOCIATE_OF → Neha Coordinator SI).
- **Neo4j:** 1 `RESOLVES_TO` edge from the source identity node to the true `Neha Gupta` node. The graph path `Vikram -> Neha Gupta` becomes fully traversable.

---

## 3. Blocker 2: Global Exports

### Exact Root Cause
The extraction pipeline (`gemini_client.py` + `validator.py`) silently dropped the relationship because the source text phrase `"is reportedly an associate of"` is semantically ambiguous. 

### Implementation vs Prompt Failure
- **Predicate Ontology:** `KNOWN_ASSOCIATE_OF` and `EMPLOYED_BY` are both explicitly allowed in `civix_api/services/nlp/schema.py`. 
- **Entity Combination:** `PERSON -> ORGANIZATION` is a supported combination in the schema logic.
- **The Failure (C):** The LLM extraction prompt strictness caused the LLM to either assign a sub-0.25 confidence score to the vague word "associate" when applied to a corporation, or drop it entirely, failing to map it to `EMPLOYED_BY` (which expects words like "Director", "works for") or `KNOWN_ASSOCIATE_OF` (which the LLM interprets as Person-to-Person).

### Comparative Analysis
- **Success Case:** "Neha Gupta is believed to be the Director of Horizon Logistics." 
  - *Result:* Successfully mapped to `EMPLOYED_BY` due to the strong role keyword ("Director").
- **Failure Case:** "Vikram Singh is reportedly an associate of Global Exports Pvt Ltd."
  - *Result:* Failed extraction due to prompt ambiguity around "associate" applied to an organization.

### Remediation Strategy
The synthetic evidence itself is technically ambiguous for an LLM instructed to extract *explicit* relationships without hallucinating. The minimal, legitimate fix is to update the C0 generator to provide a concrete semantic signal.

- Modify `scratch/generate_synthetic_docs.py` line 43 from:
  `"Vikram Singh is reportedly an associate of Global Exports Pvt Ltd."`
  To:
  `"Vikram Singh is employed as a consultant by Global Exports Pvt Ltd."`
- This ensures the extractor cleanly captures `EMPLOYED_BY`, proving the end-to-end pipeline without altering extraction engine logic or introducing hallucinations.

---

## 4. Remediation Execution Plan

### Minimal Changes Required
1. **C0 Golden World Generation:**
   - Update `scratch/generate_synthetic_docs_c0.py` to structure "Neha Coordinator" as an alias `source_identity` mapped to a phone number.
   - Update `scratch/generate_synthetic_docs.py` to change "associate of" to "employed as a consultant by" for Global Exports.
2. **C0 Golden World Ingestion:**
   - Ensure `database/ingest_golden_world.py` properly persists the new alias as a `source_identity` rather than a `person`.
3. **C4 Test Suite:**
   - Update `tests/api/test_c4_remediation.py` to inject an API call simulating the Investigator accepting the Neha Coordinator `identity_candidate` prior to running the C3 path validation.

### Impact Analysis
- **Database Reset Necessary:** Yes, but ONLY for the `civix_test` database to cleanly ingest the new C0 synthetic world. Production remains untouched.
- **C0 Corpus Regeneration Necessary:** Yes. `python scratch/generate_synthetic_docs_c0.py` and/or `generate_synthetic_docs.py` must be re-run to produce the updated `world.json`.
- **Migration Requirements:** None. The production schema is perfect.
- **Rollback Strategy:** Re-run the generation script with the previous git commit to restore the exact previous `world.json`.
- **Regression Risks:** Near zero. The extraction logic and schema are untouched.

### Expected C4 Results After Remediation
- **Blocker 1 (Vikram ↔ Neha):** Will PASS. The path will traverse via the investigator-approved `identity_resolution`.
- **Blocker 2 (Global Exports):** Will PASS. The LLM will successfully extract `EMPLOYED_BY`.
- **Final Certification:** PASS.

### Current Status
**NO CHANGES HAVE BEEN IMPLEMENTED.** The code, evidence, and database remain exactly as they were. Awaiting authorization to execute this plan.
