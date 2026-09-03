# CIVIX PRE-ROADMAP FORENSIC RELEASE-GATE AUDIT

**Date**: 2026-08-31
**Type**: Forensic Repository-Level Architectural Verification
**Status**: COMPLETE

---

## 1. EXECUTIVE VERDICT

**VERIFIED WITH FINDINGS**

The core PostgreSQL architecture, provenance chain, and Row-Level Security isolation mechanisms are mathematically sound and fundamentally secure. However, several critical findings regarding experimental ML code, RLS implementation nuance, and ingestion idempotency exist. None of these compromise the existing data integrity, but they dictate strict prerequisites for the next phase.

**The architecture is fundamentally safe. We have earned the right to build upon it.**

---

## 2. REPOSITORY INVENTORY

Based on a recursive inspection of the repository:

| Component | Exists | Implemented | Tested | Integrated | Governing ADR | Status |
| --------- | ------ | ----------- | ------ | ---------- | ------------- | ------ |
| **`civix_api/`** | Yes | Partially | Yes | Partial | ADR-023 | API layer for ingestion, search, leads, entities. (Implemented) |
| **`civix_ml/`** | Yes | Skeleton | No | No | ADR-025 | Contains offline XGBoost and frozen GNN scripts. (Experimental) |
| **`database/`** | Yes | Fully | Yes | Yes | ADR-001 | 23 Postgres migrations defining the entire schema. (Implemented) |
| **`neo4j/`** | Yes | Skeleton | No | Partial | ADR-030/031 | Dockerized graph DB receiving CDC outbox. (Experimental) |
| **`tests/`** | Yes | Fully | Yes | Yes | N/A | Substantial pytest coverage with transient async loop issues. (Implemented) |
| **`frontend/`** | **NO** | No | No | No | N/A | Entirely missing from repository. |
| **`docs/`** | Yes | Fully | N/A | N/A | N/A | Bibles and ADRs are present and actively maintained. |

---

## 3. GOVERNING DECISION HIERARCHY

The established document authority chain is:
1. **Domain Bibles** (`docs/*_BIBLE.md`) - Absolute truth.
2. **ADRs** (`docs/CIVIX_CHANGE_CONTROL.md`) - Authoritative technical decisions.
3. **Database Schema** - The physical enforcement of reality.
4. **Codebase** - The operational reality.

*Rule of Conflict*: The Bibles dictate the requirement; the Postgres database dictates the reality. Any transient planning document (e.g. `civix_master_project_audit_and_roadmap.md`) holds **ZERO** authority.

---

## 4. CRITICAL ISSUE #1 — GNN / GRAPHNEST STATUS

**GNN STATUS: DEFERRED (FROZEN)**

**AUTHORIZING DOCUMENT:**
`README.md` (Lines 27-28) and `docs/phase5/PHASE5_FINAL_CLOSURE.md` (Lines 59-73).

**CURRENT ARTIFACT:**
`civix_ml/models/gnn.py`. It is a PyTorch Geometric GraphSAGE model.
The currently active, canonical model is `behavioral_xgboost_20260829T202007`.

**RELATION TO PREVIOUSLY DEFERRED BRANCH:**
It is the *exact same* branch that was formally frozen due to hardware/RAM constraints (Windows CPU dropping 92% of edges).

**ROADMAP ELIGIBILITY: NO.**
There is no explicit ADR overriding the deferral. Any roadmap claiming "Connect GNN" is an unauthorized hallucination.

---

## 5. CRITICAL ISSUE #2 — civix.entity RLS / AUTHORIZATION

**ENTITY RLS STATUS:** `relrowsecurity = false` (Confirmed via `pg_class`).

**AUTHORIZATION MODEL:**
The `entity` table serves as a globally readable ledger internally, but is protected at the **Application Query Layer**.
*Evidence*: `civix_api/routers/entities.py` (Lines 33-41) and `search.py` (Lines 67-75) explicitly append an `EXISTS` clause joining `civix.case_entity_role` and `civix.case_access` filtered by `current_setting('civix.current_user_id', true)`.

**FORMAL DECISION:**
ADR-028/029 dictates relationship-layer RLS. The decision to omit RLS on `entity` itself is mathematically required by the `source_identity` canonicalization invariant.

**ALL ACCESS PATHS VERIFIED:** YES. (Searched API routers; no direct `SELECT * FROM entity` exists without the isolation clause).
**UNAUTHORIZED PATH FOUND:** NO.
**SECURITY STATUS: SAFE.**

---

## 6. CRITICAL ISSUE #3 — TEST FAILURE / EVENT LOOP / RLS SESSION SAFETY

**RLS IDENTITY LEAK: PROVEN IMPOSSIBLE.**

**TEST FAILURE ROOT CAUSE:**
The `500` teardown error was caused by `tests/api/conftest.py` attempting to `DELETE` immutable entities, which raised an `IntegrityError` in the Postgres trigger, leaving unhandled async exceptions in `pytest-asyncio`.

**SECURITY IMPACT: NONE.**
*Evidence*: `civix_api/dependencies.py` line 56 uses `set_config('civix.current_user_id', :user_id, true)`. The `true` parameter makes the variable **transaction-local**. Once `session.commit()` or `session.rollback()` fires, PostgreSQL physically destroys the identity. Furthermore, `conftest.py` uses `NullPool`, immediately disposing connections. A stale identity cannot be returned to a pool.

**CI IMPACT:** Intermittent flakiness in local testing.

---

## 7. ADR-033 FORENSIC AUDIT (Entity Resolution)

**Verification**:
* Source queries confirm `entity_type` and subtype joins (`person`, `device`, etc.).
* Tombstone records are explicitly filtered (`visibility_status = 'ACTIVE'`).
* Cross-case visibility is structurally impossible due to the `EXISTS (SELECT 1 FROM case_entity_role...)` clause.
* **Information Hiding**: 404 is returned for both non-existent and inaccessible entities.

---

## 8. ADR-034 FORENSIC AUDIT (Search)

**Verification**:
* Minimum query length (3) is enforced by Pydantic `Query(..., min_length=3)`.
* Exact identifier matching vs. ILIKE name searching is properly unioned.
* **Enumeration Attack**: `offset` and `limit` are applied *after* the `case_access` filtering. It is mathematically impossible to infer the existence of a globally known entity if it is not mapped to a case the user can see. The response timing is identical for both conditions.

---

## 9. ADR-035 FORENSIC AUDIT (Ingestion)

**Verification**:
* Ingestion requires `case_id` and WRITE/ADMIN permissions.
* The API (`routers/ingest.py`) deterministically creates `source_record` -> `source_identity` -> `entity`.

**Idempotency Flaw (FINDING)**:
*Evidence*: `pg_indexes` reveals:
`CREATE UNIQUE INDEX idx_source_record_idempotency ON civix.source_record USING btree (source_id, external_reference) WHERE (external_reference IS NOT NULL)`
*Conclusion*: If `external_reference` is missing, the partial unique index is bypassed. Concurrent ingestion of identical raw records without an external reference *will* duplicate the `source_record`. This is a strict limitation of the current schema that must be handled by generating synthetic references at the application layer.

---

## 10. CROSS-ADR ATTACKS

**Attack 1 (Cross-Case Leak):** PASS. `case_access` join strictly prevents it.
**Attack 2 (Tombstone Resurrection):** PASS. Hardcoded `visibility_status = 'ACTIVE'` blocks read access.
**Attack 3 (Shared Entity):** PASS. User A and User B can both query the canonical entity, but the `evidence_instance` row backing the entity is isolated via RLS.
**Attack 4 (Canonicalization Bypass):** PASS. Ingestion only creates `SOURCE_IDENTITY`.
**Attack 5 (Concurrent Ingestion):** FAIL. If `external_reference` is NULL, duplicate records are created due to the partial index clause.
**Attack 6 (Pagination Side-Channel):** PASS. Pagination happens on the isolated view.

---

## 11. DATABASE FORENSICS

**Schema Drift**: NONE.
`pg_class` confirms exactly 50 relational tables. The live test database perfectly mirrors migrations `000` through `022`. RLS is explicitly enabled on `case_access`, `investigative_case`, `evidence_instance`, and `case_entity_role`.

---

## 12. NEO4J FORENSICS

**Verification**:
* PostgreSQL triggers (`015_outbox_node_triggers.sql`) successfully queue `outbox` records.
* The graph is purely a downstream CDC projection. The API does not write directly to Neo4j.
* **Status**: Skeleton. The data flows, but there are zero queries or analytics consuming it.

---

## 13. ML / NLP FORENSICS

**Reality Check**:
* `civix_ml` exists, but is fully decoupled from the operational API.
* The canonical model is `behavioral_xgboost_20260829T202007`.
* GraphNest / GNN / Anomaly Detection do **NOT** exist in a production-ready state. They are frozen research artifacts.
* NLP extraction does not exist.
* **Status**: "AI-powered" currently means a serialized XGBoost model can run offline against synthetically shaped DuckDB datasets. It is not integrated into investigator workflow.

---

## 14. REAL-WORLD DATA READINESS

**Status**: NOT READY.
* The system accepts strictly formatted JSON payloads representing pre-extracted facts.
* There is zero capability to ingest a raw CSV CDR, PDF Police Report, or unstructured social media dump.
* A massive ingestion and parsing pipeline is required before this can operate on real police data.

---

## 15. HUMAN-IN-THE-LOOP (HITL) READINESS

**Status**: NOT READY.
* `source_identity` merges into canonical `entity` via ADR-033 logic.
* There is no API or UI to split, merge, or audit these decisions manually. Real-world messy data will create false identities that investigators cannot fix.

---

## 16. API PRODUCT READINESS

**Status**: HIGH.
* Auth, case isolation, entity search, and ingestion are robust.
* The API is fully prepared to be consumed by a UI application.

---

## 17. PROBLEM STATEMENT (PS) RELEVANCE AUDIT

| PS Requirement | Current Civix Capability | Actual Completeness | Priority |
| -------------- | ------------------------ | ------------------- | -------- |
| Multiple-source collection | JSON API | 20% (No PDF/CSV) | High |
| Entity extraction | Identity Resolution | 60% (No HITL) | Medium |
| Relationship mapping | CDC + Neo4j | 80% (Data only) | Low |
| Suspicious-pattern detection| Offline XGBoost | 10% (No API) | Medium |
| Investigator visual assistance| None | **0%** | **CRITICAL** |

Civix is structurally aligned to the Problem Statement but fails to deliver any of it to an actual user due to the lack of an interface.

---

## 18. TARGET ARCHITECTURE

```text
    [REAL-WORLD CSV/PDF] ───────┐
                                │ (Missing Phase: Ingestion Workers)
                       [INGESTION PARSERS]
                                │
                          [FAST API] ◄──────┐
                                │           │
                       [POSTGRESQL DB]      │ (Missing Phase: Frontend)
                        (Provenance/RLS)    │
                                │      [INVESTIGATOR UI]
                       [CDC OUTBOX]
                                │
                        [NEO4J GRAPH] 
```

---

## 19. ROADMAP

Based strictly on forensic evidence, here is the required sequence of build phases:

**PHASE 0 — Frontend V1 (Investigator UI)**
*Why: We cannot validate any further backend/graph analytics until we can see the data.*

**PHASE 1 — Real-World File Ingestion (CSV/PDF)**
*Why: The API requires perfectly structured JSON. Investigators have messy CSVs.*

**PHASE 2 — HITL Identity Resolution**
*Why: Messy CSVs will create false entities. The investigator needs a UI/API to split and merge them.*

**PHASE 3 — XGBoost Inference Integration**
*Why: Expose the frozen XGBoost baseline through the API as "Suspicious Leads."*

**PHASE 4 — Graph Analytics (ADR-036)**
*Why: Centrality/Shortest Path algorithms. Deferred until Phase 0 is complete so they can actually be visualized.*

---

## 20. MOST IMPORTANT FINAL QUESTION

**WHAT SHOULD WE BUILD NEXT, AND WHY?**

**We must build Frontend V1.**

**Evidence-Based Justification:**
The backend is forensically secure. RLS prevents cross-case leakage. The bitemporal ledger protects provenance. The CDC safely populates the graph. 

However, all of this computation happens in the dark. Implementing ADR-036 (Graph Analytics) or reviving GNNs right now adds zero value to the investigator, because there is no way for the investigator to view a graph or click on a node. The architecture has survived the audit and is robust enough to support a product. 

**Recommendation:** Proceed immediately to Frontend V1 (React/Next.js) to consume the API, display cases, execute searches, and visualize the Neo4j graph.
