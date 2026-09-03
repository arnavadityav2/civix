# CIVIX MASTER PROJECT AUDIT & ROADMAP

**Date:** 2026-08-31
**Role:** Principal Systems Architect
**Objective:** Complete repository-level audit and master implementation roadmap.

---

## 1. EXECUTIVE SUMMARY

Civix possesses an exceptionally secure, robust, and law-enforcement-grade backend architecture. The implementation of bitemporal data models, Row-Level Security (RLS) case isolation, provenance tracking, and an idempotent outbox pattern feeding a Neo4j graph represents a state-of-the-art foundation for intelligence analysis. 

However, **Civix currently delivers zero investigator value because it has no frontend.** It is an advanced, headless data-governance engine. While the ML components exist structurally, they are disconnected from the API and user workflows. 

The primary recommendation of this audit is an immediate pivot to **Phase E (Frontend Transformation)** before advancing any further down the backend/ML pipeline (e.g., ADR-036). We must visualize the intelligence we are currently capturing.

---

## 2. CURRENT ARCHITECTURE

The implemented architecture successfully establishes a secure data flow from raw ingestion to canonical entities, synchronized safely to a graph database.

```text
Raw Sources (FIR, CDR)
     ↓
Ingestion (ADR-035 Idempotent Ledger)
     ↓
Raw / Provenance Layer (source_record)
     ↓
Source Identity (source_identity)
     ↓
Identity Resolution (ADR-033)
     ↓
Canonical Entities (person, phone, organization)
     ↓
Case / Evidence Layer (evidence_instance, case_entity_role)
     ↓
PostgreSQL (Secure Relational Ledger)
     ↓
Outbox (CDC Queue via triggers)
     ↓
CDC Worker (Async Node/Edge extraction)
     ↓
Neo4j (Graph Database)
     ↓
[MISSING] Graph Analytics / ML (ADR-036)
     ↓
API (Partial - Cases, Leads, Entities)
     ↓
[MISSING] Frontend
     ↓
[MISSING] Investigator
```

---

## 3. PROJECT COMPONENT INVENTORY

| Component | Current State | Purpose | Dependencies | Risk | Completeness |
| --------- | ------------- | ------- | ------------ | ---- | ------------ |
| **PostgreSQL Schema** | Verified | Core Relational Ledger | None | Low | 95% |
| **RLS/Security** | Verified | Case Isolation | Postgres | Low | 100% |
| **Outbox/CDC** | Verified | Sync to Neo4j | Postgres | Low | 90% |
| **Neo4j Schema** | Initialized | Graph Mapping | CDC | Medium | 30% |
| **FastAPI Backend** | Partial | REST API | Postgres | Low | 60% |
| **ML Models (GNN)** | Skeleton | Anomaly Detection | Neo4j | High | 15% |
| **Frontend** | Non-existent | User Experience | API | Critical | 0% |
| **Documentation** | Excellent | Governance (ADRs/Bibles) | None | Low | 95% |

---

## 4. ADR RECONCILIATION

| ADR | Intended Decision | Actual Implementation | Conflicts | Status |
| --- | ----------------- | --------------------- | --------- | ------ |
| ADR-026 | Investigative Leads | Fully Implemented | None | VERIFIED |
| ADR-028/029 | RLS & Security | Fully Implemented | None | VERIFIED |
| ADR-030/031 | Graph Projection | Fully Implemented (CDC) | None | VERIFIED |
| ADR-033 | Entity Resolution | Fully Implemented | None | VERIFIED |
| ADR-034 | Secure Search | Partially Implemented | Requires UI | VERIFIED |
| ADR-035 | Ingestion | Implemented & Remediated | None | VERIFIED |
| ADR-036 | Graph Analytics | Not Implemented | Pending Audit | PLANNED |

---

## 5. DATABASE FORENSICS

**Migrations ↔ Actual Database**
The live schema perfectly matches the 23 migration files.
- **Constraints/Provenance:** Excellent. `civix.source_record` idempotency race condition was remediated via `idx_source_record_idempotency`.
- **RLS Posture:** Verified. Core business domains (`investigative_case`, `evidence_instance`, `investigative_lead`) are properly isolated using `has_case_access`.
- **Entity Identity:** `civix.entity` intentionally omits RLS (Outcome A) to act as a global canonical ledger, relying safely on `case_entity_role` for authorization visibility.

---

## 6. SECURITY / THREAT MODEL

| ID | Severity | Attack | Result | Impact | Recommendation |
| -- | -------- | ------ | ------ | ------ | -------------- |
| SEC-01 | LOW | Cross-Case Entity Search | 404/Empty (Passed) | None | Architecture is secure. |
| SEC-02 | LOW | Tombstone Retrieval | 404/Empty (Passed) | None | Provenance holds. |
| SEC-03 | MEDIUM | Event Loop Finalization | 500 on Teardown | Test Flakiness | Refactor `pytest-asyncio` DB teardown (Tech Debt). |

---

## 7. PROVENANCE & DATA INTEGRITY

**Trace:**
`Raw CDR JSON -> civix.source_record -> civix.source_identity -> Canonical civix.phone_number -> civix.case_entity_role -> Neo4j Node`

Civix can definitively answer: *"Where did this fact come from?"* 
Every edge and node in Neo4j maps back to an immutable `source_record_id` and `evidence_instance`. The provenance layer is world-class.

---

## 8. REAL-WORLD DATA READINESS

| Source | Supported Now | Parser | Validation | Case Mapping | Entity Extraction | Production Ready |
| ------ | ------------- | ------ | ---------- | ------------ | ----------------- | ---------------- |
| **JSON/API** | Yes | Pydantic | Strong | Yes | Yes | Demo Ready |
| **CDR (CSV)**| No | Missing | None | No | No | Not Ready |
| **FIR (PDF)**| No | Missing | None | No | No | Not Ready |

**Missing Architecture:** A dedicated asynchronous file-processing pipeline (e.g., Celery + OCR/Text Extraction) is required to parse raw CSVs and PDFs into the JSON structures the API currently accepts.

---

## 9. ENTITY & IDENTITY RESOLUTION AUDIT

The backend logic for canonicalization (ADR-033) is sound. It properly maps `source_identity` to canonical `entity` references. 
**Gap:** There is no human-in-the-loop (HITL) capability. Real-world messy data inevitably causes false positives. An API endpoint and UI interface to *split* or *merge* canonical identities is critical before production.

---

## 10. ML / NLP AUDIT

| Model | Input | Output | Training Data | Inference Path | Frontend Integration | Production Ready |
| ----- | ----- | ------ | ------------- | -------------- | -------------------- | ---------------- |
| **GNN Baseline**| Neo4j | Anomaly Score | Synthetic | Offline Script | Missing | Not Ready |

**Evaluation:** ML exists purely as a technical experiment in `civix_ml`. It does not contribute investigator value because predictions are not surfaced through the API or UI, and confidence/explainability are absent.

---

## 11. GRAPH / NETWORK ANALYTICS AUDIT

Neo4j is currently acting as a replica of Postgres (via the CDC outbox). 
**Gap:** We are not running Graph algorithms (Centrality, Shortest Path) on this data. ADR-036 aims to solve this, but without a UI to visualize the network, the graph analytics will remain invisible headless queries.

---

## 12. API AUDIT

The API provides solid RESTful boundaries for Cases, Entities, Leads, and Search. 
**Gap:** It lacks the interactive traversal endpoints (e.g., `GET /api/v1/entities/{id}/network`) required to power a visual graph explorer.

---

## 13. FRONTEND AUDIT

**FRONTEND GAP MATRIX**

| Capability | Backend Exists | ML Exists | API Exists | Frontend Exists | Priority |
| ---------- | -------------- | --------- | ---------- | --------------- | -------- |
| Case Mgmt | Yes | N/A | Yes | **NO** | CRITICAL |
| Search | Yes | N/A | Yes | **NO** | CRITICAL |
| Graph Viz | Yes (Data) | Partial | No | **NO** | CRITICAL |
| ML Insights | No | Partial | No | **NO** | HIGH |

The frontend is entirely missing. This is the single largest deficit in the project.

---

## 14. PS RELEVANCE MATRIX

| PS Requirement | Civix Capability | Completeness | Improvement Needed |
| -------------- | ---------------- | ------------ | ------------------ |
| Collect multiple sources | Ingestion API | 50% | Need CSV/PDF extraction. |
| Extract Entities | Entity Resolution | 80% | Need HITL Merge/Split. |
| Build Relationship Maps | CDC + Neo4j | 60% | Need Visualizer (UI). |
| Detect suspicious patterns| ML GNN | 15% | Need API Integration. |
| Assist investigators visually| None | **0%** | **CRITICAL GAP.** |

**Verdict:** Civix is structurally perfectly aligned with the Problem Statement, but operationally failing the visual/investigator requirement.

---

## 15. PRODUCT DIFFERENTIATION OPPORTUNITIES

**Evidence-Backed Graph Visualization:** Most tools show a generic graph. Civix should allow a user to click an edge in the graph and see the *exact police report or CDR* that proves the relationship. The backend provenance supports this; the frontend must execute it.

---

## 16. END-TO-END USER JOURNEY

1. Investigator logs in. **[BREAKS - No UI]**
2. Uploads real-world data (CSV). **[BREAKS - Only JSON API]**
3. System validates/preserves records. [PASS]
4. Identity Resolution. [PASS]
5. Graph Updated via CDC. [PASS]
6. Investigator explores graph. **[BREAKS - No UI]**

---

## 17. PERFORMANCE/SCALABILITY AUDIT

- **PostgreSQL/Ingestion:** Production Ready (Bitemporal + Idempotency).
- **Graph Sync:** Production Ready (Outbox pattern).
- **Files/Data:** Prototype (Lacks S3/Blob storage mapping).

---

## 18. TESTING AUDIT

- **Isolation Tests:** VERIFIED (Scenario A/B/D adversarial tests pass).
- **Test Flakiness:** HIGH (Connection leak teardown issues in Pytest).

---

## 19. DEPLOYMENT READINESS

**Classification:** Advanced Prototype.
The backend is Docker-ready, but missing the frontend, OCR pipelines, and ML serving layers required for production.

---

## 20. TECHNICAL DEBT REGISTER

| ID | Area | Finding | Severity | Recommendation |
| -- | ---- | ------- | -------- | -------------- |
| TD-01 | Testing | Pytest Asyncio Loop Leaks | MEDIUM | Refactor conftest teardowns. |
| TD-02 | Config | Hardcoded secrets in tests | LOW | Move to standard `.env` mocking. |

---

## 21. TARGET ARCHITECTURE

```text
                    ┌─────────────────────┐
                    │      FRONTEND       │
                    │ Investigator UI     │
                    │ Graph Explorer      │
                    │ ML Alert Dashboard  │
                    └──────────┬──────────┘
                               │
                         REST / GraphQL
                               │
                    ┌──────────▼──────────┐
                    │      API LAYER      │
                    │ FastAPI / Celery    │
                    └─────────┬─┬─────────┘
                              │ │
              ┌───────────────┘ └────────────────┐
              │                                  │
         PostgreSQL                            Neo4j
    (Provenance / RLS)                  (Relationship Maps)
              │                                  │
              └───────── CDC OUTBOX ─────────────┘
```

---

## 22. MASTER ROADMAP

**Phase E — Frontend Transformation (RECOMMENDED NEXT)**
*Build the Investigator Command Center, Search, and Graph Visualizer using React/Next.js to consume the existing API.*

**Phase A — Real-World Ingestion Pipeline**
*Build the asynchronous Celery pipeline to accept raw CSV CDRs and PDF FIRs, parsing them into the JSON ingestion format.*

**Phase D — Graph Analytics (ADR-036)**
*Now that the UI exists to display it, implement Graph centrality, shortest path, and community detection APIs.*

**Phase C — ML / NLP Integration**
*Connect the GNN anomaly models to the frontend as "AI Generated Leads."*

---

## 23. PRIORITY MATRIX

| Candidate | PS Value | User Value | Dependency | Risk Reduction | Priority |
| --------- | -------: | ---------: | ---------: | -------------: | -------: |
| **Frontend V1** | 10 | 10 | None | 9 | **1** |
| ADR-036 (Graph) | 8 | 2 | Needs UI | 2 | 2 |
| File Ingestion | 9 | 8 | Needs API | 4 | 3 |
| ML Integration | 7 | 6 | Needs UI | 3 | 4 |

---

## 24. RECOMMENDED NEXT STEP: FRONTEND TRANSFORMATION

**WHAT SHOULD WE BUILD NEXT?**
We must immediately halt backend development and initiate **FRONTEND V1**.

**Why?**
The backend is a masterpiece of data governance, but it is a black box. Implementing ADR-036 (Graph Analytics) right now would merely add more headless API endpoints that no human can see or interact with. To satisfy the Problem Statement ("Assist investigators by providing visual and analytical insights"), we must build the interface.

**What it unlocks:**
The ability to actually demo the product, validate that the API contracts are ergonomic, and visually verify the CDC Graph sync.

---

## 25. FRONTEND V1 STRATEGY

**Scope:**
1. **Command Center:** Dashboard of active cases and recent leads.
2. **Global Search:** Typeahead integration with the secure search view.
3. **Entity Profile:** 360-degree view of an entity (provenance, attributes).
4. **Interactive Graph:** React-Force-Graph integration pulling from Neo4j (via API) to visually explore networks.

*We will use standard modern web tooling (Vite/React/Tailwind) and strictly connect it to the live FastAPI instance.*

---

## 26. FINAL SCORECARD

| Dimension | Score | Reason |
| --------- | ----: | ------ |
| Architecture | 9.5 | World-class provenance and RLS. |
| Security | 9.0 | Verified under adversarial conditions. |
| Graph/Data Model | 8.5 | Perfectly synced; analytics missing. |
| ML/NLP | 3.0 | Exists only as standalone script. |
| Frontend | 0.0 | Does not exist. |
| **PS Alignment** | 8.0 | Structurally aligned, visually failing. |

**CURRENT CIVIX LEVEL:** Advanced Prototype.

---

## 27. FINAL ARCHITECTURAL VERDICT

The Civix backend is **VERIFIED** and robust. However, the project is currently unbalanced. To fulfill the original Problem Statement, the immediate and sole priority must be the construction of a polished, interactive Frontend application that brings the hidden graph intelligence into the light.

```text
Files modified: NONE
Database modified: NONE
Migrations modified: NONE
API modified: NONE
ML modified: NONE
Frontend modified: NONE
Neo4j modified: NONE
Tests modified: NONE
```
