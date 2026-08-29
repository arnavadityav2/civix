# CIVIX Documentation Index
**Version**: 1.0 | **Date**: 2026-08-29 | **Status**: AUTHORITATIVE

This index is the entry point for all CIVIX project documentation.
New agents MUST read `00_CIVIX_MASTER_CONTEXT.md` first, then the relevant Bible for their task.

## Quick Navigation

| # | File | Purpose | Status |
|---|---|---|---|
| — | `CIVIX_CONTEXT_INDEX.md` | **This file** — navigation index | LIVE |
| — | `CIVIX_CHANGE_CONTROL.md` | Architecture decision log + change control | LIVE |
| 00 | `00_CIVIX_MASTER_CONTEXT.md` | Master context for new agents — **READ FIRST** | LIVE |
| 01 | `01_PROJECT_VISION.md` | Purpose, goals, SIH 2026 context | LIVE |
| 02 | `02_SYSTEM_ARCHITECTURE_BIBLE.md` | Full system architecture — layers, tech stack | LIVE |
| 03 | `03_DATABASE_SCHEMA_BIBLE.md` | Every table, column, FK, constraint | LIVE |
| 04 | `04_DATA_MODEL_AND_ONTOLOGY.md` | Entity ontology, type hierarchies | LIVE |
| 05 | `05_EPISTEMIC_MODEL.md` | Evidence → Observation → Extraction → Assertion pipeline | LIVE |
| 06 | `06_IDENTITY_RESOLUTION_BIBLE.md` | SourceIdentity → Person resolution model | LIVE |
| 07 | `07_FORENSICS_AND_MEDICAL_BIBLE.md` | Forensic + medical evidence architecture | LIVE |
| 08 | `08_SPATIOTEMPORAL_MODEL.md` | PostGIS, temporal model, cell sectors | LIVE |
| 09 | `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md` | Provenance chain, custody, risk | LIVE |
| 10 | `10_SECURITY_RBAC_AUDIT_BIBLE.md` | Users, roles, access control, audit | LIVE |
| 11 | `11_AI_ML_BIBLE.md` | AI pipeline, feature extraction, leakage prevention | LIVE |
| 12 | `12_SYNTHETIC_DATA_BIBLE.md` | Synthetic world, Golden World, scenario factory | LIVE |
| 13 | `13_NEO4J_GRAPH_BIBLE.md` | Neo4j projection, graph model, tombstones | LIVE |
| 14 | `14_POSTGRESQL_BIBLE.md` | PostgreSQL schema strategy, partitioning, RLS | LIVE |
| 15 | `15_API_BACKEND_BIBLE.md` | API design, backend architecture | STATUS: OPEN — Not yet designed |
| 16 | `16_FRONTEND_BIBLE.md` | Frontend architecture | STATUS: OPEN — Not yet designed |
| 17 | `17_LEGAL_COMPLIANCE_BIBLE.md` | Legal restrictions, expungement, data governance | LIVE |
| 18 | `18_TESTING_VALIDATION_BIBLE.md` | Test strategy, adversarial tests, golden world regression | LIVE |
| 19 | `19_IMPLEMENTATION_MASTER_PLAN.md` | Phase-by-phase implementation plan | LIVE |
| 20 | `20_DECISIONS_AND_CHANGELOG.md` | Architectural decision records | LIVE |
| 21 | `21_KNOWN_GAPS_AND_RISKS.md` | Open gaps, risks, deferred items | LIVE |

## Frozen Artifacts (DO NOT MODIFY WITHOUT EXPLICIT AUTHORIZATION)

| File | Location | Purpose |
|---|---|---|
| `synthetic_world.md` | `~/.gemini/.../brain/.../synthetic_world.md` | Canonical CIVIX world specification v2.1 |
| `ground_truth.json` | `output/ground_truth.json` | Generator ground truth labels |
| `config.py` | `civix_generator/config.py` | Canonical expected counts |

## Superseded / Pre-Hardening Files (DO NOT USE FOR IMPLEMENTATION)

| File | Location | Problem |
|---|---|---|
| `schema_postgres.sql` | `database/schema_postgres.sql` | Pre-hardening. Stores `password_hash` in users table. No epistemic model. No bitemporal. SUPERSEDED. |
| `schema_neo4j.cypher` | `database/schema_neo4j.cypher` | Pre-hardening. Does not reflect reviewed architecture. SUPERSEDED. |

## Current Implementation Gate

```
READY FOR DDL
```

See `03_DATABASE_SCHEMA_BIBLE.md` and `19_IMPLEMENTATION_MASTER_PLAN.md` for DDL execution order.
