# CIVIX 2.0 CANONICAL PROJECT STATE
**Last Updated**: 2026-08-31

## 1. Purpose
This document records the verified current state of CIVIX 2.0, overriding all historical scratchpads and transient conversational documents.

## 2. Authority Model
1. **Design Authority**: `docs/CIVIX_CHANGE_CONTROL.md` and Domain Bibles. *Overrides all planning.*
2. **Implementation Authority**: Actual production codebase and database schema.
3. **Acceptance Authority**: Live acceptance test results.
4. **Planning Authority**: `docs/19_IMPLEMENTATION_MASTER_PLAN.md`.
5. **Historical Artifacts**: Files in `brain/` or `docs/archive/` possess ZERO authority.

## 3. Canonical Architecture State
- **PostgreSQL / Outbox / CDC / Neo4j Projection**: COMPLETE & LIVE VERIFIED. Neo4j graph rules formally DECIDED (ADR-030).
- **Security / RLS**: DB-level COMPLETE. API-level formal requirements DECIDED (ADR-028, ADR-029).
- **API Read Layer**: PARTIALLY COMPLETE. Architecture formally DECIDED (ADR-026, ADR-027). Awaiting schema migration for Lead Persistence before implementation resumes.
- **ML Layer**: PARTIALLY COMPLETE (Feature Gen / Graph Inference built; Anomaly detection needs verification).

## 4. Capability Ledger
| Capability | Status |
| --- | --- |
| PostgreSQL Schema & Migrations | LIVE VERIFIED |
| Bitemporal Model & Triggers | LIVE VERIFIED |
| Row-Level Security (RLS) | LIVE VERIFIED |
| CDC & Outbox Synchronization | LIVE VERIFIED |
| Neo4j Graph Projection | LIVE VERIFIED |
| API Authentication (JWT) | TESTED |
| API Case/Lead Endpoints | TESTED |
| API Entity/Hypothesis Endpoints | MISSING |
| Audit & Expungement APIs | MISSING |
| ML Graph Features & Inference | TESTED |
| ML Anomaly Detection | NEEDS VERIFICATION |
| Synthetic World Factory | BLOCKED |

## 5. Phase Ledger
- **Phases 1-5**: COMPLETE
- **Phase 7 (Graph Write)**: COMPLETE
- **Phase 8 (API)**: PARTIALLY COMPLETE
- **Phase 9 (Security)**: PARTIALLY COMPLETE
- **Phase 10 (ML)**: NEEDS VERIFICATION / PARTIAL
- **Phase 11 (Scale Factory)**: BLOCKED
- **Phase 12 (Adversarial Testing)**: PLANNED (Decoupled from Phase 8 API completion)

## 6. Completion Rules
- An ADR authorizes a framework/decision; it **does not** prove implementation completion.
- A plan does not prove implementation completion.
- A passing unit test does not automatically establish live acceptance.
- A phase cannot be marked complete merely because its framework exists.

## 7. Historical Artifact Rule
Historical planning artifacts (e.g., files in `brain/` or archives) cannot create requirements, phases, steps, dependencies, or completion status. "Phase 7 Step 7" is explicitly deprecated.

## 8. Conflict Escalation Rule
If authoritative sources (e.g., Code vs Bibles) disagree, DO NOT GUESS. Record the contradiction and escalate for human resolution.

## 9. Agent Context Rule
Future AI agents MUST read this document first. Agents are strictly prohibited from using transient scratchpads as instructions.

## 10. Last Verified State
Snapshot as of 2026-08-31. Any new agent entering this repository must treat this file as the paramount ground truth.
