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
