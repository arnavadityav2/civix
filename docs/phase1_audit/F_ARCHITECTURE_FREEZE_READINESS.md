# F — ARCHITECTURE FREEZE READINESS
## CIVIX Phase 1 — Final Implementation Gate

**Date**: 2026-08-29 | **Auditor**: Adversarial Architecture Review Agent

---

## Verdict

> [!CAUTION]
> ## **NOT READY**
> 
> CIVIX is **NOT ready** for PostgreSQL/Neo4j implementation.
> 
> There are **5 CRITICAL blockers** that make it impossible to write correct DDL.
> There are **9 HIGH blockers** that would produce a semantically incomplete or broken schema.
> There are **4 ADVERSARIAL TEST FAILURES** (ADV-15, ADV-16, ADV-19, ADV-22) indicating architectural gaps.
>
> All 5 CRITICAL blockers require explicit human decisions or schema changes before any migration file is written.

---

## Critical Blockers (Must resolve before Migration 02)

| Blocker | Description | Resolution |
|---|---|---|
| **BLK-01** | 5 ENUM types undefined (`hypothesis_status_enum`, `lead_priority_enum`, `lead_status_enum`, `task_type_enum`, `task_status_enum`) | Human must confirm ENUM values → update `03_DATABASE_SCHEMA_BIBLE.md` |
| **BLK-02** | `ground_truth.json` is empty `{}` | Human must decide: populate it, or document as intentionally empty |
| **BLK-03** | `source_identity.extraction_id` contradicts ADR-006 | Remove column; write ADR-019 |
| **BLK-04** | `[:CONTRADICTS]` in Neo4j is self-contradictory with ADR-007 | Write ADR-013; replace with `[:HAS_STANCE]` |
| **BLK-05** | LOC-* location coordinates undefined (blocks ingestion design) | Create `location_master.json` OR define fallback strategy |

---

## High Blockers (Must resolve before Phase 3 completion)

| Blocker | Description |
|---|---|
| **BLK-06** | hypothesis_support has no bitemporal versioning (stance changes cannot be audited) |
| **BLK-07** | evidence_instance requires pre-existing case — operational ordering constraint undefined |
| **BLK-08** | case_access UNIQUE(case_id, user_id) prevents permission level history |
| **BLK-09** | civix_user single role decision needed |
| **BLK-10** | Expungement does not address free-text PII in lead/hypothesis/assertion text |
| **BLK-11** | CCTV/media entity structured metadata undefined |
| **BLK-12** | evidence_artifact missing `classification_level` field for intelligence reports |
| **BLK-13** | observation.observed_by FK to civix_user cannot represent field officers |
| **BLK-14** | validators.py defaults disagree with config.py (vehicles: 18 vs 13, accounts: 24 vs 29) |

---

## Adversarial Test Failures (Architecture defects requiring resolution)

| Test | Failure | Impact |
|---|---|---|
| **ADV-15** | Chain of custody gap not representable in MVP | Accepted — deferred to Phase 2 forensics |
| **ADV-16** | Conflicting lab results not representable in MVP | Accepted — deferred to Phase 2 forensics |
| **ADV-19** | Assertions have no case-level access control | **HIGH** — cross-case assertion access is ungated |
| **ADV-22** | Faulty analysis_run cannot be invalidated | **HIGH** — no `status` on analysis_run; no assertion supersession |

---

## What IS Ready

The following architectural components are **sound and can proceed to DDL** as-is (after Critical blockers are resolved):

| Component | Status | Notes |
|---|---|---|
| Entity supertype model | ✅ READY | ADR-001 implemented correctly |
| Assertion epistemic model | ✅ READY | ADR-002 implemented; stance separation correct |
| Source → Evidence chain | ✅ READY | Correct structure, correct immutability rules |
| Identity resolution pipeline | ✅ READY | merge/split events correct |
| SIM temporal constraints | ✅ READY | GIST exclusion correctly designed |
| Account holder temporal | ✅ READY | valid_time TSTZRANGE correct |
| Property mutation (H4) | ✅ READY | N-ary event via event_participant correctly resolves H4 |
| Audit event immutability | ✅ READY | append-only trigger design correct |
| Outbox pattern | ✅ READY | ADR-008 correctly implemented |
| Evidence deduplication | ✅ READY | UNIQUE(hash, algorithm) per ADR-004 |
| Predicate vocabulary | ✅ READY | predicate_enum defined and complete |
| Hypothesis AI-confirmation guard | ✅ READY | DB CHECK constraint correct |
| provenance risk computation | ✅ READY | INV-11: dynamic, never stored |
| Cell tower as polygon | ✅ READY | ADR-009 correctly documented |
| civix_user no-password | ✅ READY | ADR-010 correctly documented |
| Synthetic data isolation | ✅ READY | generation_run_id filter pattern correct |

---

## Conditions for READY Status

The architecture may be declared READY when ALL of the following are true:

### Gate 1 — Critical Blockers Resolved
- [x] `hypothesis_status_enum` defined with confirmed values
- [x] `lead_priority_enum` defined with confirmed values
- [x] `lead_status_enum` defined with confirmed values
- [x] `task_type_enum` defined with confirmed values
- [x] `task_status_enum` defined with confirmed values
- [x] `ground_truth.json` status determined (populated or accepted as empty)
- [x] `source_identity.extraction_id` removed; ADR-019 written (Note: became ADR-014)
- [x] Neo4j relationship design changed to `[:HAS_STANCE]`; ADR-013 written (Note: became ADR-015)
- [x] LOC-* location coordinate strategy decided and documented (ADR-016)

### Gate 2 — High Blockers Resolved (or explicitly deferred with documented rationale)
- [ ] `hypothesis_support` bitemporal versioning decided; ADR-012 written
- [ ] `evidence_instance` case-first ordering documented in `12_SYNTHETIC_DATA_BIBLE.md`
- [ ] `case_access` UNIQUE constraint fixed to partial index
- [ ] `civix_user` single-role decision documented; ADR-018 written
- [ ] Expungement free-text PII decision documented; ADR-017 written
- [ ] CCTV metadata strategy decided (JSONB or separate table)
- [ ] `evidence_artifact.classification_level` field added
- [ ] `observation.observer_entity_id` field decision made; ADR-015 written
- [ ] `validators.py` defaults corrected to match `config.py`

### Gate 3 — Medium Changes Completed
- [ ] All 12 TEXT-should-be-ENUM fields converted in schema Bible
- [ ] `assertion.object_location_id` removed
- [ ] `case_entity_role` temporal fields upgraded to TIMESTAMPTZ + tx_start
- [ ] Provenance indexes documented in Migration 18
- [ ] FIR status field added

### Gate 4 — ADRs Written
- [x] ADR-012 through ADR-016 written and recorded in `CIVIX_CHANGE_CONTROL.md`
- [ ] ADR-017 through ADR-019 (For Gate 2 items) still pending

### Gate 5 — Bible Updated
- [x] `03_DATABASE_SCHEMA_BIBLE.md` updated to reflect Critical changes
- [x] `13_NEO4J_GRAPH_BIBLE.md` updated for HAS_STANCE relationship
- [ ] `03_DATABASE_SCHEMA_BIBLE.md` updated for High changes
- [ ] `21_KNOWN_GAPS_AND_RISKS.md` updated with Phase 1 findings
- [ ] `10_SECURITY_RBAC_AUDIT_BIBLE.md` updated with RLS for classification level

---

## Recommended Next Actions (Ordered)

### Immediate (This Session)
1. User confirms or modifies proposed ENUM values for BLK-01 (**5 minutes**)
2. User decides on ground_truth.json strategy — BLK-02 (**5 minutes**)
3. User approves removal of `extraction_id` from source_identity — BLK-03 (**2 minutes**)
4. User approves `[:HAS_STANCE]` Neo4j relationship — BLK-04 (**2 minutes**)
5. User decides LOC-* coordinate strategy — BLK-05 (**5 minutes**)
6. User decides on hypothesis_support bitemporal and assertion.case_id — BLK-06, ADV-19 (**10 minutes**)
7. User decides on civix_user single-role (MVP: accept Option A) — BLK-09 (**2 minutes**)
8. User decides on expungement free-text PII (MVP: accept risk) — BLK-10 (**2 minutes**)
9. User decides on CCTV metadata (MVP: JSONB column) — BLK-11 (**2 minutes**)

### Next Session (Schema Bible Update)
10. Write ADR-012 through ADR-019
11. Update `03_DATABASE_SCHEMA_BIBLE.md` with all CHANGE-01 through CHANGE-22
12. Update `13_NEO4J_GRAPH_BIBLE.md` with HAS_STANCE
13. Update `21_KNOWN_GAPS_AND_RISKS.md` with Phase 1 findings
14. Update `CIVIX_CHANGE_CONTROL.md` with new ADRs

### After Schema Bible Update
15. Re-run Phase 1 gate check (verify all 5 gates satisfied)
16. If all gates pass: declare ARCHITECTURE FREEZE
17. Begin Phase 2 (PostgreSQL Logical Model / ERD)
18. Only then begin Phase 3 (PostgreSQL Physical DDL)

---

## Estimated Time to READY

| Activity | Estimated Time |
|---|---|
| User decisions (9 items above) | ~35 minutes |
| Writing 8 new ADRs | ~30 minutes |
| Updating 03_DATABASE_SCHEMA_BIBLE.md | ~60 minutes |
| Updating other Bibles | ~30 minutes |
| Final gate check | ~15 minutes |
| **Total estimated to FREEZE** | **~3 hours** |

---

## Positive Assessment

Despite the blockers, the CIVIX architecture has made **substantial progress** compared to the original schema (which was a flat relational model without epistemic separation, identity resolution, or provenance).

The following are genuine architectural achievements that will survive into the final implementation:
- The bitemporal model is correctly designed
- The epistemic pipeline (Source → Observation → Event → Assertion → Hypothesis) is correctly separated
- The identity resolution model (SourceIdentity → Candidate → Resolution → Person) is robust
- The N-ary event model solves H4 correctly
- The evidence deduplication model (artifact + instance) is correct
- The outbox synchronization pattern prevents split-brain with Neo4j
- The predicate vocabulary prevents free-text pollution
- The hypothesis AI-guard prevents AI from autonomously declaring guilt

The remaining blockers are specific, well-defined, and mostly require human decisions rather than architectural rethinking. Once those decisions are captured, the path to DDL is clear.

---

## Formal Verdict

```
╔══════════════════════════════════════════════════════════════════╗
║  CIVIX ARCHITECTURE FREEZE STATUS: NOT READY                     ║
║                                                                  ║
║  Critical Blockers: 5 (all require human decision)              ║
║  High Blockers: 9 (all require human decision or schema change)  ║
║  ADVersarial FAILs: 4 (2 accepted-deferred, 2 must be fixed)    ║
║                                                                  ║
║  INSTRUCTION: Resolve blockers in the order listed above.        ║
║  Once Gate 1 through Gate 5 are satisfied, re-run this audit.   ║
║  Do NOT begin DDL until this document says READY.                ║
╚══════════════════════════════════════════════════════════════════╝
```
