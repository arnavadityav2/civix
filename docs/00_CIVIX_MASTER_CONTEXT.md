# 00 — CIVIX Master Context
## First Document for Any New Agent or Engineer

**Version**: 1.0 | **Date**: 2026-08-29 | **Phase**: Pre-DDL (READY FOR DDL)

> [!IMPORTANT]
> Read this document completely before touching any code, schema, or documentation.
> This document is the ground truth for what CIVIX is, what has been done, and what must be done next.
> The chat history is NOT a reliable context source. This file is.

---

## 1. What Is CIVIX?

CIVIX is an **AI-powered investigative intelligence platform** built for **Smart India Hackathon (SIH) 2026**.

Its purpose: ingest heterogeneous law-enforcement data (CDRs, financial transactions, surveillance, property records, forensic evidence, medical records) and help investigators discover:

- Hidden criminal networks and relationships
- Suspicious temporal and spatial patterns
- Cross-case connections
- Anomalies in financial and communication data
- Contradictory and exculpatory evidence

**CIVIX is decision-support software. It does NOT replace investigator judgment.**

---

## 2. Current Phase

```
PHASE: Pre-DDL Implementation
GATE STATUS: READY FOR DDL

Completed:
  ✅ Phase 3 — Synthetic World Generation & Validation
  ✅ Phase 4B — Discrepancy Resolution & Generator Closure
  ✅ Phase 5A — Adversarial Architecture Review (50 scenarios)
  ✅ Phase 5B — MVP Schema Design v1 + v2
  ✅ Pre-DB Freeze Audit — 16 gaps identified
  ✅ Schema Hardening — All 25 gaps (16 original + 9 new) resolved

In Progress:
  📝 Phase 0 — Documentation & Context Consolidation (THIS PHASE)

Not Started:
  ⬜ Phase 1 — Architecture Reconciliation
  ⬜ Phase 2 — PostgreSQL Logical Model (DDL begins here)
  ⬜ Phase 3 — PostgreSQL Physical Schema
  ...
```

---

## 3. Frozen Artifacts

These files must NEVER be modified without an explicit ADR entry in `CIVIX_CHANGE_CONTROL.md`:

| File | Location | Why Frozen |
|---|---|---|
| `synthetic_world.md` | `brain/.../synthetic_world.md` | Canonical CIVIX world v2.1. Generator regression anchor. |
| `ground_truth.json` | `output/ground_truth.json` | ML ground truth labels. Modification = training data corruption. |
| `config.py` | `civix_generator/config.py` | Canonical expected record counts. |

**Superseded files (DO NOT USE):**
- `database/schema_postgres.sql` — Pre-hardening. No epistemic model. Stores passwords. SUPERSEDED.
- `database/schema_neo4j.cypher` — Pre-hardening. Does not match reviewed architecture. SUPERSEDED.

---

## 4. Repository Structure

```
civix 2.0/
├── civix_generator/          # Synthetic data generation pipeline
│   ├── world/
│   │   ├── models.py         # Python dataclasses for world entities
│   │   ├── loader.py         # Loads canonical world from synthetic_world.md
│   │   ├── golden_world.py   # Golden World deterministic rules
│   │   └── parser.py         # World YAML/MD parser
│   ├── events/               # Per-domain event generators
│   │   ├── cdr_gen.py        # CDR generation (385 records)
│   │   ├── finance_gen.py    # Transaction generation (50 records)
│   │   ├── property_gen.py   # Property transfer generation (3 records)
│   │   ├── vehicle_gen.py    # Vehicle sighting generation (8 records)
│   │   ├── surveillance_gen.py
│   │   ├── intelligence_gen.py
│   │   └── case_gen.py       # Criminal history records (6 records)
│   ├── lineage/
│   │   └── lineage.py        # Record provenance tracker
│   ├── tests/                # Pytest test suite
│   │   ├── test_golden_world.py
│   │   ├── test_world.py
│   │   ├── test_phase3c.py
│   │   ├── test_phase3d.py
│   │   └── test_phase4b_negative.py
│   ├── config.py             # ⛔ FROZEN — expected counts
│   ├── generator.py          # Main entry point
│   └── validators.py         # Cross-domain validation
├── output/                   # Generated synthetic data (CSV/JSON)
│   ├── cdrs.csv              # 385 CDR records
│   ├── transactions.csv      # 50 financial transactions
│   ├── vehicle_sightings.csv # 8 sightings
│   ├── surveillance_reports.json # 12 reports
│   ├── intelligence_reports.json # 5 reports
│   ├── criminal_history_records.csv # 6 records
│   ├── property_transfers.csv # 3 transfers
│   ├── ground_truth.json     # ⛔ FROZEN
│   └── lineage.json          # Record lineage/provenance
├── database/                 # ⚠️ SUPERSEDED — do not use for implementation
│   ├── schema_postgres.sql   # Pre-hardening SQL — SUPERSEDED
│   └── schema_neo4j.cypher   # Pre-hardening Cypher — SUPERSEDED
├── docs/                     # ✅ AUTHORITATIVE documentation (THIS DIRECTORY)
│   ├── CIVIX_CONTEXT_INDEX.md
│   ├── CIVIX_CHANGE_CONTROL.md
│   ├── 00_CIVIX_MASTER_CONTEXT.md  (this file)
│   └── ... (see CIVIX_CONTEXT_INDEX.md)
├── count_entities.py         # Utility: count entities in output
└── patch.py                  # Phase 4B patch utility
```

---

## 5. The Synthetic World (Golden World v2.1)

55 people across three criminal networks, with hidden cross-network connections the system must discover.

**Three Networks**:
- **Network Alpha** — Drug Distribution (Jaipur–Ajmer Corridor): Vikram (P-01), Amit (P-02), Priya (P-05), Ravi (P-06), Suresh (P-03), Irfan (P-07), Dinesh (P-11)
- **Network Beta** — Land Grab Syndicate (Ajmer–Pushkar): Harish (P-09), Neha (P-08), Deepak (P-04), Sunita (P-12), Rajendra (P-13)
- **Network Gamma** — Extortion Ring (Jaipur Commercial): Bhupendra (P-10), Arjun (P-15), Sanjay (P-16), Kavita (P-17), Rocky (P-18)

**Hidden connections** (the ones the AI must discover):
- Amit (Alpha) ↔ Harish (Beta): shared financial account
- Suresh (Alpha) bridges to Beta: same vehicle, same locations
- Ravi (Alpha) ↔ Bhupendra (Gamma): brother-in-law relationship
- Babita Devi: victim of both Alpha and Beta (land grab + intimidation)

**Validated signals** (Phase 4B closed):
- SIG-03: Suresh movement anomaly — RESOLVED
- SIG-05: Dinesh ₹3.25L corruption deposits — RESOLVED
- SIG-06: Deepak ₹75K corruption deposit — RESOLVED
- SIG-08: Bhupendra/Gopal periodic communications — RESOLVED
- FL-06: Rekha Verma false lead — RESOLVED
- H4/Babita/PROP-01+PROP-08: DEFERRED to database architecture (flat CSV cannot represent one event → two properties)

---

## 6. Architecture Principles (Non-Negotiable)

### 6.1 Epistemic Pipeline (NEVER COLLAPSE THESE LAYERS)
```
Source
  → SourceRecord          (immutable receipt)
  → Evidence              (artifact + case context)
  → Observation           (directly recorded fact)
  → Extraction            (AI inference from evidence)
  → Event                 (real-world occurrence hub)
  → Assertion             (S → P → O structured claim)
  → HypothesisSupport     (directional stance to hypothesis)
  → Hypothesis            (investigative theory)
  → InvestigativeLead     (actionable tip)
  → InvestigationTask     (human action required)
```

### 6.2 Assertion Rules
- Assertions have NO stance
- Assertions contain: Subject → Predicate → Object/Value
- `epistemic_status` on assertion = "is this claim believed to be true?" (independently)
- `hypothesis_support.stance` = "does this claim support THIS hypothesis?"
- These are DIFFERENT. Never conflate them.

### 6.3 Identity Rules
- `SourceIdentity` is the ingest target (never `Person`)
- `Person` is created only by explicit `IdentityResolutionDecision`
- Multiple `IdentityCandidate` rows per `SourceIdentity` are allowed
- Historical assertions must remain valid if identity is later split
- `Person.is_criminal` does not exist in PostgreSQL (see ADR-005)

### 6.4 Database Rules
- PostgreSQL is the authoritative source of truth
- Neo4j is an analytical projection — NEVER the authoritative source
- All Neo4j changes flow through `civix.outbox` (see ADR-008)
- `CONTRADICT` hypothesis_support rows are stored as properties in Neo4j, never as topological edges (see ADR-007)

### 6.5 Evidence Rules
- One artifact may appear in multiple cases (`EvidenceArtifact` 1:N `EvidenceInstance`)
- Hash uniqueness = `UNIQUE(sha256_hash, hash_algorithm)` (see ADR-004)
- Provenance risk is computed dynamically, never stored as a boolean flag

---

## 7. Entity Ontology Summary

All domain objects subtype from `civix.entity` (Universal Supertype):

| Entity Type | Table | Purpose |
|---|---|---|
| PERSON | `civix.person` | Canonical human (requires identity resolution) |
| SOURCE_IDENTITY | `civix.source_identity` | Unresolved identifier from raw data |
| PHONE_NUMBER | `civix.phone_number` | Telecom MSISDN |
| SIM | `civix.sim` | Physical SIM card |
| DEVICE | `civix.device` | Physical handset (IMEI) |
| FINANCIAL_ACCOUNT | `civix.financial_account` | Bank/UPI account |
| VEHICLE | `civix.vehicle` | Physical vehicle |
| PROPERTY | `civix.property` | Real estate/land |
| ORGANIZATION | `civix.organization` | Company/government body |
| NETWORK | `civix.network` | Criminal/social network |
| LOCATION | `civix.location` | PostGIS geometry (polygon, point, sector) |

---

## 8. Database Strategy

**Dual-engine architecture:**
- **PostgreSQL/PostGIS**: Authoritative system of record, bitemporal, RLS, immutable evidence, full provenance
- **Neo4j**: Analytical projection for graph traversal, hypothesis analysis, ML feature generation

**Schema**: 35+ tables in `civix` schema. See `03_DATABASE_SCHEMA_BIBLE.md`.

**DDL Migration Order** (18 migration files):
1. Extensions (PostGIS, btree_gist, uuid-ossp)
2. ENUMs
3. Users & Access
4. Source & Evidence
5. Identity
6. Domain Subtypes
7. Telecom relationships
8. Finance relationships
9. Cases
10. Epistemic pipeline
11. Workflow
12. Forensic stubs
13. Security & Legal
14. Provenance & Data Quality
15. Synthetic data control
16. RLS policies
17. Triggers (audit immutability, tombstone)
18. Indexes

---

## 9. ML Strategy Summary

- ML trains on synthetic data, not production data
- Feature extraction uses AS-OF `tx_start < snapshot_timestamp` (no future leakage)
- `generation_run_id IS NOT NULL` records are excluded from production analytics
- `ground_truth.json` is stored in `scenario.ground_truth JSONB` — never projected to Neo4j
- See `11_AI_ML_BIBLE.md` for full pipeline

---

## 10. Current Blockers

None. All 25 architecture gaps have been resolved.

See `21_KNOWN_GAPS_AND_RISKS.md` for deferred items and known risks.

---

## 11. Next Action

The next implementation agent should:
1. Read this file completely
2. Read `03_DATABASE_SCHEMA_BIBLE.md` for the exact schema
3. Read `19_IMPLEMENTATION_MASTER_PLAN.md` for the DDL execution order
4. Begin with Migration 01: `01_extensions.sql`
5. Record every implementation decision in `CIVIX_CHANGE_CONTROL.md`

Do NOT modify `synthetic_world.md`, `ground_truth.json`, `config.py`, or generator code during database implementation.

---

## 12. Document References

| Topic | Bible |
|---|---|
| Full entity + schema definitions | `03_DATABASE_SCHEMA_BIBLE.md` |
| Epistemic pipeline detail | `05_EPISTEMIC_MODEL.md` |
| Identity resolution | `06_IDENTITY_RESOLUTION_BIBLE.md` |
| Forensics & Medical | `07_FORENSICS_AND_MEDICAL_BIBLE.md` |
| Spatial/temporal | `08_SPATIOTEMPORAL_MODEL.md` |
| Provenance | `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md` |
| Security/RBAC | `10_SECURITY_RBAC_AUDIT_BIBLE.md` |
| AI/ML | `11_AI_ML_BIBLE.md` |
| Synthetic data | `12_SYNTHETIC_DATA_BIBLE.md` |
| Neo4j | `13_NEO4J_GRAPH_BIBLE.md` |
| PostgreSQL | `14_POSTGRESQL_BIBLE.md` |
| Implementation plan | `19_IMPLEMENTATION_MASTER_PLAN.md` |
| Decisions | `CIVIX_CHANGE_CONTROL.md` |
| Open gaps | `21_KNOWN_GAPS_AND_RISKS.md` |
