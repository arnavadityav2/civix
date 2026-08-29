# CIVIX Change Control & Architecture Decision Log
**Version**: 1.0 | **Date**: 2026-08-29

> [!IMPORTANT]
> Every material architectural decision MUST be recorded here before it is implemented.
> Future AI agents MUST NOT make silent architectural changes.
> If you change an architecture invariant, record it here first.

---

## Change Control Rules

1. **No silent changes**: Any change to an architecture invariant, entity definition, relationship cardinality, constraint, or predicate vocabulary must be recorded in this document before code is written.
2. **No retroactive edits**: Do not modify past decision entries. Mark old decisions as SUPERSEDED and add a new one.
3. **Frozen artifacts**: `synthetic_world.md`, `ground_truth.json`, and `config.py` require an explicit written authorization entry here before modification.
4. **Blocker escalation**: If a DDL implementation step discovers a schema contradiction, STOP. Record a new GAP entry in `21_KNOWN_GAPS_AND_RISKS.md` and in this log before proceeding.

---

## Architecture Decision Record (ADR) Format

```
ADR-NNN
Date: YYYY-MM-DD
Status: ACCEPTED | SUPERSEDED | OPEN
Problem:
Options:
Decision:
Rationale:
Consequences:
Affected Documents:
Affected Code:
```

---

## Decision Log

### ADR-001: Universal Entity Supertype
**Date**: 2026-08-28 | **Status**: ACCEPTED

**Problem**: Assertion and EventParticipant need to reference many different entity types (Person, Vehicle, Property, etc.) while preserving FK integrity. Polymorphic string-type columns sacrifice referential integrity. Multiple nullable FK columns are fragile.

**Options**:
- A. Polymorphic type+id columns (`subject_type TEXT, subject_id UUID`) — loses DB FK integrity
- B. Multiple sparse nullable FKs — explosion of columns, fragile
- C. Universal entity supertype (`civix.entity`) with subtypes sharing the PK — clean, enforced at DDL level

**Decision**: Option C — Universal Entity Supertype

**Rationale**: Single FK target (`entity_id`) allows both `assertion.subject_entity_id` and `event_participant.entity_id` to reference any entity type with full FK constraint enforcement. Subtype tables use `entity_id` as both PK and FK to `civix.entity`.

**Consequences**: Every domain object must be inserted into `civix.entity` before its subtype table. Requires application-layer coordination on insert. DDL must enforce subtype-supertype integrity via FK.

**Affected Documents**: `03_DATABASE_SCHEMA_BIBLE.md`, `04_DATA_MODEL_AND_ONTOLOGY.md`

---

### ADR-002: Assertion Has No Stance
**Date**: 2026-08-28 | **Status**: ACCEPTED

**Problem**: Earlier draft architectures placed SUPPORT/CONTRADICT on the Assertion itself. This prevents one assertion from simultaneously supporting hypothesis A and contradicting hypothesis B.

**Decision**: `assertion` has `epistemic_status` (belief in the S-P-O claim itself). `hypothesis_support` has `stance` (directional relationship to a specific hypothesis). These are different concepts.

**Consequences**: Every stance evaluation requires a `hypothesis_support` row, not an assertion field update. This is more rows but dramatically more expressive.

**Affected Documents**: `05_EPISTEMIC_MODEL.md`, `03_DATABASE_SCHEMA_BIBLE.md`

---

### ADR-003: investigative_case Not case
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: `CASE` is a SQL reserved word and would require quoting in every query.

**Decision**: Physical table name is `civix.investigative_case`. Logical/domain name remains "Case" in documentation.

**Affected Documents**: `03_DATABASE_SCHEMA_BIBLE.md`

---

### ADR-004: Hash Uniqueness Must Include Algorithm
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: `UNIQUE(sha256_hash)` would incorrectly treat the same 32 bytes under SHA-256 and SHA-3 as identical artifacts.

**Decision**: `UNIQUE(sha256_hash, hash_algorithm)` composite constraint on `evidence_artifact`.

**Rationale**: Scoping by algorithm is mathematically correct. Same bytes under different algorithms do not refer to the same file and must not be conflated.

**Affected Documents**: `03_DATABASE_SCHEMA_BIBLE.md`, `05_EPISTEMIC_MODEL.md`

---

### ADR-005: Person.is_criminal Is Prohibited
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: `models.py` contains `Person.is_criminal: Optional[bool]`. This must not map to any PostgreSQL column on the person entity.

**Decision**: No `is_criminal`, `is_suspect`, `criminal_record_count`, or similar investigative status field on `civix.person`. Case-specific roles live in `civix.case_entity_role`. Criminal determination is a hypothesis, not a person attribute.

**Rationale**: Encoding criminality as a permanent person attribute violates the fundamental CIVIX principle that "association does not equal guilt." It would also conflict with expungement requirements.

**Affected Documents**: `03_DATABASE_SCHEMA_BIBLE.md`, `06_IDENTITY_RESOLUTION_BIBLE.md`, `17_LEGAL_COMPLIANCE_BIBLE.md`

**Affected Code**: `civix_generator/world/models.py` — `Person.is_criminal` field is a generator-internal convenience; it must NOT be used as a column mapping during database ingestion.

---

### ADR-006: Provenance Table Uses Application-Enforced FKs
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: The `civix.provenance` table links derived objects (assertions, extractions, hypotheses) to source objects (observations, evidence, source records). These come from different tables, making multi-table FK constraints impossible without complex workarounds.

**Options**:
- A. Separate FK columns per entity type (7+ nullable FKs) — fragile
- B. Polymorphic type+id (no FK integrity) — loses constraint
- C. Application-enforced integrity: `derived_type/derived_id`, `source_type/source_id` — enforced at app layer

**Decision**: Option C — `derived_type TEXT, derived_id UUID, source_type TEXT, source_id UUID`. FK integrity enforced at application layer, not database layer.

**Rationale**: The provenance graph naturally spans multiple entity types. Attempting to enforce it via DB FKs requires either 7 nullable columns or a polymorphic design. The application layer emits provenance records atomically with the derived object, making app-layer enforcement reliable.

**Consequences**: Integration tests must verify provenance integrity separately from DB constraints.

**Affected Documents**: `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md`, `03_DATABASE_SCHEMA_BIBLE.md`

---

### ADR-007: CONTRADICT Edges Excluded from Graph Algorithms
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: Projecting `hypothesis_support(stance=CONTRADICT)` as a topological Neo4j edge would contaminate PageRank, Louvain community detection, and GNN traversals with negative weights that these algorithms are not designed to handle.

**Decision**: `CONTRADICT` (and `NEUTRAL`, `INCONCLUSIVE`) stance rows in `hypothesis_support` are stored as relationship properties in Neo4j (`stance: 'CONTRADICT'`). Graph algorithm queries MUST filter `WHERE r.stance = 'SUPPORT'` before invoking structural algorithms.

**Affected Documents**: `13_NEO4J_GRAPH_BIBLE.md`, `11_AI_ML_BIBLE.md`

---

### ADR-008: Outbox Pattern for Neo4j Synchronization
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: Direct dual-write to Neo4j from application code creates split-brain risk (PostgreSQL committed, Neo4j write failed = inconsistency). Database triggers calling external services are an anti-pattern.

**Decision**: All Neo4j changes flow through a `civix.outbox` table. A CDC consumer reads the outbox and applies changes to Neo4j idempotently. The outbox write is atomic with the PostgreSQL transaction.

**Required table** (not yet in DDL migration list, added as GAP-25):
```sql
civix.outbox(id UUID, entity_id UUID, action TEXT, entity_type TEXT,
             payload JSONB, created_at TIMESTAMPTZ, consumed_at TIMESTAMPTZ NULLABLE)
```

**Affected Documents**: `13_NEO4J_GRAPH_BIBLE.md`, `14_POSTGRESQL_BIBLE.md`

---

### ADR-009: Cell Tower As Polygon, Never As Point
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: CDR data contains `location_cell` fields like `CELL-01`. Earlier drafts treated these as latitude/longitude points for the user's location, creating false precision.

**Decision**: Cell IDs (`CELL-01` through `CELL-47`) map to `civix.location` rows with `location_type = CELL_SECTOR_POLYGON`. The geometry is a PostGIS polygon approximating the coverage area. If actual network data is unavailable, use `ESTIMATED_POINT` with `uncertainty_radius_meters = 5000`. Never represent cell tower centroid as the user's location in an Assertion.

**Affected Documents**: `08_SPATIOTEMPORAL_MODEL.md`, `03_DATABASE_SCHEMA_BIBLE.md`

---

### ADR-010: Authentication Credentials Never In civix_user
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: The existing `database/schema_postgres.sql` stores `password_hash` in the `users` table. This mixes authentication (auth provider responsibility) with investigative identity (CIVIX responsibility).

**Decision**: `civix.civix_user` contains only `external_auth_id` (reference to auth provider like Keycloak/Auth0), `username`, `display_name`, `role`, `clearance_level`, `is_active`. No passwords, tokens, or secrets.

**Affected Documents**: `10_SECURITY_RBAC_AUDIT_BIBLE.md`, `03_DATABASE_SCHEMA_BIBLE.md`

**Affected Code**: `database/schema_postgres.sql` is SUPERSEDED. Do not use it for implementation.

---

### ADR-012: Five Missing ENUM Types Defined
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: Five ENUM types (`hypothesis_status`, `lead_priority`, `lead_status`, `task_type`, `task_status`) were referenced in the schema but undefined.
**Decision**: Defined all five ENUMs based on cross-Bible extraction. Key values: `hypothesis_status` (ACTIVE, UNDER_REVIEW, CONFIRMED, REFUTED, ARCHIVED), `lead_status` (OPEN, IN_PROGRESS, CONFIRMED, FALSE_POSITIVE, CLOSED, DEFERRED).
**Affected Documents**: `03_DATABASE_SCHEMA_BIBLE.md`, `13_NEO4J_GRAPH_BIBLE.md`

---

### ADR-013: ground_truth.json is a Generated Placeholder
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: `ground_truth.json` is currently empty (`{}`), which appeared to block ingestion validation.
**Decision**: Formally document `ground_truth.json` as a generated placeholder that the synthetic generator does not yet populate. Phase 5 ingestion validation will use SQL COUNT queries against PostgreSQL `generation_run_id` rows, not file-level JSON comparison.
**Affected Documents**: `12_SYNTHETIC_DATA_BIBLE.md`, `18_TESTING_VALIDATION_BIBLE.md`

---

### ADR-014: Remove extraction_id from source_identity
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: `source_identity.extraction_id` creates a direct DB FK for provenance, contradicting ADR-006 which mandates application-enforced provenance records.
**Decision**: Removed `extraction_id` from `source_identity`. AI derivations will write a record to `civix.provenance(derived_type='SOURCE_IDENTITY', source_type='EXTRACTION')`.
**Affected Documents**: `03_DATABASE_SCHEMA_BIBLE.md`, `09_PROVENANCE_CHAIN_OF_CUSTODY_BIBLE.md`

---

### ADR-015: HAS_STANCE Replaces SUPPORTS/CONTRADICTS
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: Neo4j Bible defined `[:CONTRADICTS]` as a separate relationship type, contradicting ADR-007 (which requires stance as a property) and contaminating structural algorithms.
**Decision**: Replaced `[:SUPPORTS]` and `[:CONTRADICTS]` with a single `[:HAS_STANCE]` relationship type carrying a `stance` property. Structural graph algorithms must filter `WHERE stance = 'SUPPORT'`.
**Affected Documents**: `13_NEO4J_GRAPH_BIBLE.md`, `11_AI_ML_BIBLE.md`

---

### ADR-016: Location Master for LOC-* and CELL-*
**Date**: 2026-08-29 | **Status**: ACCEPTED

**Problem**: The synthetic data references `LOC-01` through `LOC-30` and `CELL-01` through `CELL-47` but provides no coordinate definitions, blocking PostGIS ingestion.
**Decision**: Create a derived, non-frozen `location_master.json` containing synthetic PostGIS coordinates in Ajmer district for all LOC and CELL entities.
**Affected Documents**: `08_SPATIOTEMPORAL_MODEL.md`, `12_SYNTHETIC_DATA_BIBLE.md`

---

## Frozen Artifact Change Requests

No frozen artifact changes have been authorized. Any request to modify `synthetic_world.md`, `ground_truth.json`, or `config.py` must be logged here with explicit justification before action is taken.

### ADR-017: Assertion Case Authorization Array
**Date**: 2026-08-29
**Decision**: Add `authorized_case_ids UUID[]` to `civix.assertion` to prevent recursive RLS timeouts.

### ADR-018: Strict Entity Tombstoning
**Date**: 2026-08-29
**Decision**: Prevent physical `DELETE` on `civix.entity` using triggers. Mandate `visibility_status = 'TOMBSTONED'`.

### ADR-019: Bitemporal Append-Only Triggers
**Date**: 2026-08-29
**Decision**: Enforce `tx_end` closures and automatic `INSERT` on `UPDATE` via PostgreSQL triggers for all bitemporal tables.

### ADR-020: Artifact Cryptographic Garbage Collection
**Date**: 2026-08-29
**Decision**: Mandate `ON DELETE RESTRICT` from instance to artifact.

### ADR-021: Financial Account Roles
**Date**: 2026-08-29
**Decision**: Implement fully bitemporal `financial_account_role`.

### ADR-022: Derived Evidence Hierarchy
**Date**: 2026-08-29
**Decision**: Add `parent_artifact_id` to `evidence_artifact` with `ON DELETE RESTRICT`.
