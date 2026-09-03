# 20 — Decisions & Changelog
**Version**: 1.0 | **Date**: 2026-08-29

> This file tracks the changelog of documentation updates.
> Architecture decisions (ADRs) live in `CIVIX_CHANGE_CONTROL.md`.
> This file tracks when documentation was changed and why.

---

## Documentation Changelog

### 2026-08-29 — Phase 0: Initial Documentation System Created

**Author**: Antigravity AI (CIVIX project agent)

**Changes**:
- Created `docs/` directory
- Created all 23 documentation files (Bibles + control files)
- Migrated all architecture decisions from chat history to ADR log
- Captured all 25 resolved gaps in `21_KNOWN_GAPS_AND_RISKS.md`
- Documented supersession of `database/schema_postgres.sql` and `database/schema_neo4j.cypher`
- Consolidated architecture invariants (INV-01 through INV-20)

**Key decisions captured**:
- ADR-001: Universal entity supertype
- ADR-002: Assertion has no stance
- ADR-003: investigative_case not case
- ADR-004: Hash uniqueness includes algorithm
- ADR-005: Person.is_criminal prohibited
- ADR-006: Provenance uses app-enforced FKs
- ADR-007: CONTRADICT edges excluded from graph algorithms
- ADR-008: Outbox pattern for Neo4j sync
- ADR-009: Cell tower as polygon
- ADR-010: Auth credentials never in civix_user

**Phase 4B closures documented**:
- SIG-03, SIG-05, SIG-06, SIG-08, FL-06 — all CLOSED
- H4/Babita — formally deferred to database architecture (RESOLVED there)

**Open decisions left explicitly unresolved** (intentional):
- Backend framework
- Frontend framework
- CDC consumer technology
- ORM strategy
- ML model architecture
- Data retention periods
- Acceptable Neo4j lag
- Clearance enforcement mechanism

---

## Future Changelog Entries

Add entries here whenever:
- A Bible document is substantially updated
- An ADR is added or superseded
- A phase is completed
- A gap is discovered and resolved
- A frozen artifact is modified (requires ADR first)

Format:
```
### YYYY-MM-DD — [Description]
Author: [who made the change]
Changes: [what was changed and why]
Documents affected: [list of files]
ADR: [ADR reference if applicable]
```

### 2026-08-31 — Project-Wide Documentation Forensic Reconciliation
**Author**: Antigravity AI (Agent A)
**Changes**:
- Reconciled Phase 7 task numbering conflicts. Recorded that the engineering sprint labeled "Phase 7 Tasks 1-3" executed Master Plan Phases 8, 9, and 10 out of order.
- Added retrospective ADRs for FastAPI, SQLAlchemy AsyncSession, and XGBoost to formally authorize the architecture that was already successfully implemented.
- Removed false blockers from `21_KNOWN_GAPS_AND_RISKS.md` and `19_IMPLEMENTATION_MASTER_PLAN.md`.
- Formally marked Phase 7 Task 1, 2, and 3 as COMPLETE and ACCEPTED.
**Documents affected**: `CIVIX_CHANGE_CONTROL.md`, `21_KNOWN_GAPS_AND_RISKS.md`, `19_IMPLEMENTATION_MASTER_PLAN.md`, `CANONICAL_PHASE_7_HANDOVER.md`
**ADR**: ADR-023, ADR-024, ADR-025

### 2026-08-31 — System Bibles Governance Alignment (Agent B Remediation)
**Author**: Antigravity AI (Agent A)
**Changes**:
- Removed the false "OPEN DECISION" statuses for Backend framework, ORM, and ML/AI architectures across the primary Bibles.
- Aligned current architectural statements with the verified implementation state and the retrospective ADRs (ADR-023 for FastAPI, ADR-024 for SQLAlchemy Async, and ADR-025 for XGBoost).
- This resolves the split-brain governance state identified during the independent governance acceptance audit.
**Documents affected**: `02_SYSTEM_ARCHITECTURE_BIBLE.md`, `11_AI_ML_BIBLE.md`, `15_API_BACKEND_BIBLE.md`
**ADR**: ADR-023, ADR-024, ADR-025
