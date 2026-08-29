# 02 — System Architecture Bible
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE

> [!NOTE]
> This document describes the complete system architecture. Read `00_CIVIX_MASTER_CONTEXT.md` first.

---

## 1. Architecture Philosophy

CIVIX uses a **layered, dual-engine architecture**:

```
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SOURCES                           │
│  Telecom CDRs │ Bank Transactions │ Police FIRs │ CCTV         │
│  Property Registry │ Forensic Labs │ Medical Records │ OSINT   │
└───────────────────────────┬─────────────────────────────────────┘
                            │ (ingest)
┌───────────────────────────▼─────────────────────────────────────┐
│           POSTGRESQL (Authoritative System of Record)           │
│                                                                 │
│  Source → SourceRecord → Evidence → Observation → Extraction   │
│     → Event → Assertion → Hypothesis → Lead → Task             │
│                                                                 │
│  + Identity Resolution + Cases + Forensics + Medical           │
│  + Spatial (PostGIS) + Temporal (TSTZRANGE) + Audit + RLS      │
└────────────────────────────┬────────────────────────────────────┘
                             │ (outbox → CDC)
┌────────────────────────────▼────────────────────────────────────┐
│                      NEO4J (Analytical Projection)              │
│                                                                 │
│  Graph Traversal │ Network Analysis │ Hypothesis Engine        │
│  PageRank │ Louvain │ Temporal Slices │ GNN Feature Extraction │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      BACKEND / API                              │
│              Python / FastAPI (STATUS: OPEN DECISION)          │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                      FRONTEND                                   │
│         React / Next.js (STATUS: OPEN DECISION)                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Relational DB | PostgreSQL 16+ with PostGIS, btree_gist | DECIDED |
| Graph DB | Neo4j 5+ | DECIDED |
| Spatial | PostGIS (GEOMETRY type, SRID 4326) | DECIDED |
| Temporal | PostgreSQL `TSTZRANGE` + `btree_gist` exclusion | DECIDED |
| CDC/Sync | Outbox pattern → CDC consumer | DECIDED |
| Auth | External provider (Keycloak/Auth0) + civix_user table | DECIDED |
| ORM | STATUS: OPEN DECISION | |
| Backend | STATUS: OPEN DECISION | |
| Frontend | STATUS: OPEN DECISION | |
| Container | Docker Compose (dev), Kubernetes (production) | PLANNED |
| ML/AI | STATUS: OPEN DECISION — Python-based, likely PyTorch | |

---

## 3. Critical Architectural Rules

### 3.1 PostgreSQL is Authoritative
PostgreSQL is the only database where data is written from application code.
Neo4j receives data ONLY through the outbox → CDC pipeline.
No dual-write pattern. No direct Neo4j write from application code.

### 3.2 Neo4j is an Analytical Projection
Neo4j is reconstructable from PostgreSQL at any time.
If Neo4j is lost or corrupted, replay the outbox.
Neo4j may be stale by up to [STATUS: OPEN DECISION — acceptable lag TBD].

### 3.3 Epistemic Layers Must Not Collapse
```
Source → SourceRecord → Evidence → Observation → Extraction → Event → Assertion → Hypothesis
```
Skipping layers (e.g., `Source → Assertion`) is forbidden.
Mixing layers (e.g., stance on Assertion) is forbidden.

### 3.4 Exculpatory Evidence is First-Class
Negative findings (DNA exclusion, verified alibi, contradicting assertion) must be represented as first-class `hypothesis_support(stance=CONTRADICT)` rows. They must not be hidden or de-prioritized.

---

## 4. Data Flow Diagram

```
RAW CDR ROW
     ↓
source_record (immutable receipt)
     ↓
evidence_instance (case-scoped artifact context)
     ↓
observation (caller=X, callee=Y, duration=Z)
     ↓
extraction (AI: confidence=0.87 that X=Person P-01)
     ↓
event (CALL event, occurred_at=[start, start+duration])
     ↓
event_participant (CALLER: source_identity X, CALLEE: source_identity Y, CELL_TOWER: CELL-17)
     ↓
assertion (X CALLED Y, epistemic_status=CONFIRMED, valid_from=call_start)
     ↓
hypothesis_support (assertion A1 SUPPORTS hypothesis H3, weight=0.8)
     ↓
hypothesis (H3: "P-01 and P-02 are coordinating drug runs")
     ↓
investigative_lead (L7: "P-01 and P-02 had 12 calls on Aug 13 — unusually high")
     ↓
investigation_task (T22: "Interview P-01's contact P-02")
```

---

## 5. Synthetic Data System

The CIVIX synthetic world is a controlled test environment with known ground truth.

It is NOT a placeholder. It IS the SIH demonstration dataset.

See `12_SYNTHETIC_DATA_BIBLE.md` for full details.
Current cardinalities: 55 persons, 3 networks, 16 orgs, 385 CDRs, 50 transactions, etc.

---

## 6. Security Architecture

- PostgreSQL Row-Level Security (RLS) enforces case-level access
- `case_access` table is the basis for RLS policies
- Auth provider (external) → `civix.civix_user` (investigative identity only)
- `audit_event` is append-only (enforced by DB trigger)
- Expunged records: invisible via RLS in PostgreSQL; physically deleted from Neo4j via TOMBSTONE

See `10_SECURITY_RBAC_AUDIT_BIBLE.md` for full details.

---

## 7. Known Architecture Decisions

See `CIVIX_CHANGE_CONTROL.md` for the full ADR log (ADR-001 through ADR-010 as of this document version).
