# C4 Remediation Plan Revision

## 1. Executive Summary
This document revises the remediation plan based on a deep-dive verification of the C2 deterministic engine rules, the NLP extraction ontology, and the API surface. The revised plan strictly preserves the frozen synthetic evidence and focuses purely on production code fixes (extraction prompting, resolution rules) and extending the C4 test contract to simulate the existing investigator HITL requirement.

---

## 2. Issue 1: C2 Rule & Investigator Resolution Contract

### C2 Implementation Reality
- **Existing Rules:** The C2 engine (`civix_api/services/entity_resolver.py`) implements exactly four rules: `RULE_01_NAME_PHONE`, `RULE_02_NAME_ACCOUNT`, `RULE_03_ALIAS_VEHICLE`, and `RULE_04_NAME_ORG`.
- **The Defect:** `RULE_01_NAME_PHONE` requires an **exact normalized name match** (`tsn.norm_name = tpn.norm_name`). "NEHACOORDINATOR" does not match "NEHAGUPTA". Therefore, even if ingested correctly as a `source_identity`, the current C2 engine will **NOT** generate a candidate.

### API & Contract Reality
- **Investigator Resolution API:** C2 *does* expose an investigator resolution API (`POST /api/v1/identities/resolve` in `civix_api/routers/identity.py`), which correctly inserts into `civix.identity_resolution` and triggers the Neo4j `RESOLVES_TO` projection.
- **C4 Contract:** Simulating investigator approval in the C4 test suite represents a **CONTRACT CHANGE**. The existing `test_c4_remediation.py` assumes the graph path is automatically traversable without simulating HITL intervention. 

### Revised Remediation Strategy (Blocker 1)
Instead of modifying the synthetic evidence, we will fix the code and test contract:
1. **Fix Ingestion (Code Fix):** Update `ingest_golden_world.py` to ingest "Neha Coordinator" as a `source_identity` linked to her phone number.
2. **Add C2 Rule (Code Fix):** Add `RULE_05_PHONE_ONLY` to `entity_resolver.py` to generate candidates based purely on a shared phone number assertion, regardless of name exactness.
3. **Extend C4 Test (Contract Change):** Add an API call in `test_c4_remediation.py` to POST to `/api/v1/identities/resolve`, simulating an investigator accepting the candidate *before* evaluating the path.

---

## 3. Issue 2: Global Exports Evidence

### Ontology Reality
- **Predicate Support:** `KNOWN_ASSOCIATE_OF` is explicitly defined in `civix_api/services/nlp/schema.py` (`ALLOWED_PREDICATES`).
- **Entity Constraints:** Neither `schema.py` nor `entity_mapper.py` restricts `KNOWN_ASSOCIATE_OF` exclusively to `PERSON -> PERSON`. The pipeline programmatically accepts `PERSON -> ORGANIZATION`.
- **The Defect:** The failure is purely an LLM extraction strictness issue. The LLM either applies a sub-0.25 confidence score to "associate" when applied to a corporation, or drops it because the prompt does not explicitly instruct it to use `KNOWN_ASSOCIATE_OF` for corporations.

### Revised Remediation Strategy (Blocker 2)
The existing evidence ("Vikram Singh is reportedly an associate of Global Exports Pvt Ltd.") is semantically sufficient for the ontology. Changing it is unjustified.
1. **Fix Extraction Prompt (Code Fix):** Update the `LLM_OUTPUT_SCHEMA_DESCRIPTION` instructions in `civix_api/services/nlp/schema.py` to explicitly state: *"KNOWN_ASSOCIATE_OF may be used between a PERSON and an ORGANIZATION if they are described as an 'associate of' the organization."*
2. **Preserve Evidence (Data Preservation):** Do not modify `scratch/generate_synthetic_docs.py` or the Golden World.

---

## 4. Decision Table

| Blocker | Existing Evidence Sufficient? | Existing C2/NLP Contract Supports It? | Minimal Legitimate Fix | Changes Evidence? | Changes Production Code? | Changes C4 Contract? | Classification |
|---------|-------------------------------|----------------------------------------|-------------------------|-------------------|-------------------------|----------------------|----------------|
| **1 (Neha)** | YES (but ingested wrong) | NO (Missing RULE_05_PHONE_ONLY) | Fix C0 Ingestion + Add C2 Rule + Simulate HITL API | NO | YES | YES | DATA PRESERVATION + CODE FIX + CONTRACT CHANGE |
| **2 (Global Exports)** | YES | YES (Ontology allows it) | Update Gemini Prompt Instructions | NO | YES | NO | DATA PRESERVATION + CODE FIX |

---

## 5. Authorization Boundary
- **Status:** PLAN REVIEW ONLY.
- **Implemented:** NO.
- **Next Steps:** Awaiting explicit authorization to implement the CODE FIXES and CONTRACT CHANGE described above, followed by re-running the C0 pipeline and C4 tests on the `civix_test` database.
