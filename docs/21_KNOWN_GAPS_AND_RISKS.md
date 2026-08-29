# 21 — Known Gaps & Risks
**Version**: 1.0 | **Date**: 2026-08-29 | **Updated with every new finding**

---

## Gap Status Legend

| Status | Meaning |
|---|---|
| CLOSED | Resolved in architecture documents |
| DEFERRED | Intentionally deferred to a later phase |
| OPEN | Requires decision before implementation |
| ACCEPTED | Known risk, accepted by project owner |

---

## Architecture Invariants Register (INV-01 through INV-20)

| INV | Invariant | Enforced By |
|---|---|---|
| INV-01 | Assertion has no stance | Schema design; code review |
| INV-02 | EntityCluster is never an assertion target | Application layer |
| INV-03 | SourceIdentity.raw_identifier is immutable | Application layer; no UPDATE trigger |
| INV-04 | EvidenceArtifact uniqueness = (hash, algorithm) | UNIQUE constraint |
| INV-05 | One event may target many entities | No entity FKs on event table |
| INV-06 | One artifact → many case instances | EvidenceInstance has case_id |
| INV-07 | Person never auto-created from SourceIdentity | Application layer; IdentityResolution required |
| INV-08 | AI cannot autonomously confirm a hypothesis | DB CHECK constraint |
| INV-09 | PostgreSQL is authoritative; Neo4j is derived | Architecture pattern; outbox only |
| INV-10 | CONTRADICT stance never a topological graph edge | Neo4j projection rules |
| INV-11 | Provenance risk is computed, never stored | No `tainted BOOL` column anywhere |
| INV-12 | Legal restrictions ≠ deletion in PostgreSQL | RLS + physical retention |
| INV-13 | Audit events are append-only | DB trigger |
| INV-14 | Synthetic ground_truth never projected to Neo4j | Projection filter |
| INV-15 | SIM physical constraints differ from person-use | GIST on sim_in_device, not on assertions |
| INV-16 | Network membership ≠ guilt | No guilt inference from network membership |
| INV-17 | is_criminal must not exist on Person | Schema review; DDL validation |
| INV-18 | Free-text predicates are banned | predicate_enum enforced |
| INV-19 | Cell tower centroid ≠ user location | Data quality rules; no SEEN_AT from cell data |
| INV-20 | Outbox is the only Neo4j sync mechanism | No direct Neo4j write in application code |

---

## Closed Gaps (From Pre-DB Audit + Hardening Report)

| Gap ID | Description | Resolved In |
|---|---|---|
| GAP-01 | civix_user undefined | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-02 | case table undefined | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-03 | data_quality_issue missing | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-04 | evidence_instance.case_id missing | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-05 | identity_merge/split_event missing | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-06 | sim_number_assignment missing | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-07 | account_holder missing | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-08 | case_entity_role incomplete | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-09 | case_access missing | `03_DATABASE_SCHEMA_BIBLE.md` |
| GAP-12 | Evidence hash uniqueness wrong | ADR-004 |
| GAP-13 | Predicate vocabulary missing | `03_DATABASE_SCHEMA_BIBLE.md` ENUM section |
| GAP-14 | Confidential informant protection | `source.is_identity_protected` field |
| GAP-17 | Person.is_criminal must not map to DB | ADR-005, INV-17 |
| GAP-18 | Vehicle-only sightings not supported | event_participant role=DRIVER optional |
| GAP-19 | Org-name account IDs in transactions.csv | Source_identity ingest mapping documented |
| GAP-20 | UNKNOWN-IMEI in CDRs | Source_identity ingest mapping documented |
| GAP-21 | event.location_id direct FK wrong | Location is event_participant(LOCATION) |
| GAP-22 | hypothesis confirmed_by constraint missing | DB CHECK constraint defined |
| GAP-23 | CONTRADICT edges contaminate graph algorithms | ADR-007, INV-10 |
| GAP-24 | sim_number_assignment GIST exclusion missing | Constraint defined in schema |
| GAP-25 | Outbox table undefined | Table defined in Migration 13 |

---

## Deferred Items

| Item | Phase | Notes |
|---|---|---|
| H4/Babita PROP-01+PROP-08 | Phase 5 (ingestion) | Correctly represented via event_participant(TARGET_PROPERTY). H4 represents a Phase 3 CSV limitation — resolved by DB architecture. |
| Full forensic model | Phase 2 | MVP stubs only in Phase 1. 20 tables fully architectured. |
| SIM table cardinalities | Phase 5 | Not explicitly enumerated in Golden World — will be derived during ingestion. |
| Juvenile auto-restriction trigger | Phase 9 | DB trigger or application logic TBD |
| CDC consumer implementation | Phase 7 | Message broker not yet chosen |
| Data retention policies | Phase 9 | Legal review required |
| RLS for protected sources | Phase 9 | Exact policy not yet designed |
| Partitioning strategy | Phase 3 | Apply before 10M rows/table |
| ML training pipeline | Phase 10 | Technology stack not yet chosen |
| Frontend framework | Phase 8 | Not yet decided |
| Backend framework | Phase 8 | Not yet decided |
| Synthetic World Factory | Phase 11 | Not yet designed |
| Performance targets | Phase 12 | Subject to hardware constraints |

---

## Known Risks

| Risk | Severity | Mitigation |
|---|---|---|
| `database/schema_postgres.sql` accidentally used for implementation | HIGH | Marked SUPERSEDED in docs; DDL comes only from migration files |
| AI agent making silent architectural changes | HIGH | `CIVIX_CHANGE_CONTROL.md` ADR log mandatory |
| Generator run changes frozen counts | MEDIUM | Tests enforce counts; frozen files marked |
| Cell tower data unavailable for polygon generation | MEDIUM | Fall back to ESTIMATED_POINT with uncertainty_radius_meters |
| Split-brain between PostgreSQL and Neo4j | MEDIUM | Outbox pattern; CDC consumer idempotent |
| Identity auto-merge from high confidence score | HIGH | DB design + application rule: human decision required |
| `is_criminal` field from models.py leaking into DB | HIGH | ADR-005 + INV-17 document prohibition; ingestion code review |

---

## Open Questions (Architecture)

| Question | Who decides | Priority |
|---|---|---|
| Acceptable Neo4j lag | Project owner | HIGH |
| CDC consumer: Kafka vs Redis vs pg_notify | Tech lead | HIGH |
| Backend framework | Tech lead | HIGH |
| ORM strategy | Tech lead | MEDIUM |
| Exact clearance enforcement mechanism | Security review | MEDIUM |
| Retention period per data category | Legal review | MEDIUM |
| ML model architecture | ML lead | LOW (Phase 10) |
| Frontend graph visualization library | UX lead | LOW (Phase 8) |

## Phase 1 Gate 3 Final Resolutions
- **BLK-15 to BLK-22**: Resolved via strict DB-level enforcement (RLS arrays, append-only triggers, tombstone triggers, ON DELETE RESTRICT).
- **Scale Risk**: Large UUID[] arrays on assertions may hit TOAST table limits if an assertion belongs to thousands of cases. Unlikely in investigative context, but accepted risk.
