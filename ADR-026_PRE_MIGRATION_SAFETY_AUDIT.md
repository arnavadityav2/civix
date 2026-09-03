# ADR-026 PRE-MIGRATION SAFETY AUDIT

## 1. EXISTING LEAD DATA
**Analysis:** There are ZERO existing `civix.investigative_lead` rows in the repository's synthetic data or seed fixtures. 
- A comprehensive `grep` across `database/ingest_golden_world.py`, `database/generate_large_dataset.py`, and `tests/` confirmed no `INSERT INTO civix.investigative_lead` statements exist.
- The `Rekha Verma` lead mentioned in the Master Plan is currently generated *ephemerally* by the XGBoost model in `civix_api/routers/leads.py` and returned as a JSON payload; it is never written to the database.
**Conclusion:** Migration is 100% safe regarding existing data. No backfill or data fabrication is required because no data exists to be migrated.

## 2. TARGET ENTITY NULLABILITY
**Analysis:** `docs/03_DATABASE_SCHEMA_BIBLE.md` defines `target_entity_id` as `NOT NULL`. Furthermore, `docs/11_AI_ML_BIBLE.md` strictly dictates: "ML-generated recommendations... must target a specific entity (`target_entity_id`)." 
**Conclusion:** `target_entity_id` MUST be `NOT NULL` for ALL investigative leads. A lead fundamentally represents an investigatory theory *about a specific entity* within a case.

## 3. HYPOTHESIS NULLABILITY
**Analysis:** `docs/03_DATABASE_SCHEMA_BIBLE.md` defines `hypothesis_id` as `UUID FK→hypothesis NULL`. The ML Bible indicates ML generates leads from hypotheses (Hypothesis → Lead), but the Schema Bible allows it to be NULL.
**Conclusion:** `hypothesis_id` MUST be `NULLABLE`. This permits human investigators to create general case leads that are not strictly bound to a formalized hypothesis, while application logic can still mandate it for ML-generated leads.

## 4. CROSS-CASE CONSISTENCY
**Analysis:** If a lead belongs to Case A and points to a hypothesis, that hypothesis MUST belong to Case A. 
Currently, PostgreSQL does not enforce `lead.case_id = hypothesis.case_id` directly, because the `hypothesis_id` FK points to the `hypothesis` primary key alone.
**Most Consistent Architectural Approach:**
Instead of relying on application logic or introducing procedural triggers, PostgreSQL can enforce this relationally by:
1. Adding a unique constraint to the hypothesis table: `ALTER TABLE civix.hypothesis ADD CONSTRAINT uq_hypothesis_case UNIQUE (hypothesis_id, case_id);`
2. Using a composite foreign key on the lead table: `FOREIGN KEY (hypothesis_id, case_id) REFERENCES civix.hypothesis (hypothesis_id, case_id);`
This approach perfectly aligns with relational integrity conventions and guarantees cross-case consistency at the database level with zero overhead.

## 5. OUTBOX TRIGGER — FULL FORENSIC REVIEW
**Current Definition for Leads:**
```sql
    ELSIF TG_TABLE_NAME = 'investigative_lead' THEN
        v_entity_id := NEW.lead_id;
        v_entity_type := 'investigative_lead';
        v_payload := jsonb_build_object(
            'lead_id', NEW.lead_id,
            'case_id', NEW.case_id,
            'lead_text', NEW.lead_text,
            'priority', NEW.priority,
            'status', NEW.status
        );
```
**Current State:**
- The payload lacks `target_entity_id` and `hypothesis_id`.
- The CDC consumer passes this to `_upsert_node` in `civix_api/services/neo4j_projection.py`.
- `_upsert_node` merges a standalone `(n:Lead {lead_id: ...})` node and sets the properties.
- **Critical Gap:** The current trigger and consumer do not generate *any* graph edges linking the Lead to the Entity, Hypothesis, or even the Case.
**ADR-026 Requirements:** 
The trigger MUST be updated to include `target_entity_id` and `hypothesis_id` in the `v_payload`.

## 6. NEO4J IMPACT
**Analysis:** Adding IDs to the JSON payload is not enough to create graph edges. `civix_api/services/neo4j_projection.py` currently routes `investigative_lead` outbox events to the generic `_upsert_node` method, which only updates node properties.
**Conclusion:** 
- **Payload changes:** Required in PostgreSQL trigger.
- **New graph edges:** Required (e.g., `(Lead)-[:TARGETS]->(Entity)`, `(Lead)-[:SUPPORTS]->(Hypothesis)`).
- **Changed projection logic:** `neo4j_projection.py` MUST be updated to include a dedicated `_upsert_investigative_lead` method (similar to `_upsert_assertion`) that explicitly `MATCH`es the target entity/hypothesis and `MERGE`s the relational edges.

## 7. MIGRATION NUMBER
**Analysis:** The `database/migrations/` directory contains exactly 20 migration files, ordered `000` through `019`. The highest numbered migration is `019_outbox_epistemic_and_edge_triggers.sql`.
**Conclusion:** Migration `020` is genuinely available and is the correct next integer.

## 8. INDEX JUSTIFICATION
- **`idx_lead_target_entity`**: **REQUIRED**. Required for efficiently querying all leads associated with a specific entity (e.g., `GET /entities/{id}/leads`). Filtering by RLS (`case_id IN ...`) requires the DB to first isolate the entity's leads before applying case-level visibility.
- **`idx_lead_hypothesis`**: **RECOMMENDED**. Highly beneficial for `GET /cases/{id}/hypotheses/{id}/leads`, but given the relatively small number of leads per case, a composite index on `(case_id, hypothesis_id)` might be marginally better. However, a direct index on `hypothesis_id` is standard for foreign keys to prevent full table scans during deletion cascades or reverse lookups.

## 9. AUDIT + BITEMPORAL IMPACT
**Analysis:** 
- `civix.investigative_lead` is not a bitemporal table (it uses standard `status` updates and `disposition_notes`).
- Audit trails for leads are enforced by application-level inserts into `civix.audit_event` (action: `LEAD_DISPOSITION`), not by database triggers (verified by inspecting `011_triggers.sql`).
- The only trigger on `investigative_lead` is the outbox trigger.
**Conclusion:** Adding these columns does not break or require changes to audit, bitemporal, or immutability invariants.

## 10. FINAL MIGRATION SAFETY VERDICT
**READY WITH CONDITIONS**

Conditions:
1. The migration must include the composite FK strategy to enforce `lead.case_id = hypothesis.case_id`.
2. The migration must update the outbox trigger to include the new IDs in the payload.
3. The Neo4j projection logic (`neo4j_projection.py`) must be updated alongside the migration to actually materialize the graph edges for leads.

## 11. MOST IMPORTANT OUTPUT: Safest Migration Strategy

The safest migration strategy that brings the ACTUAL database into ADR-026 compliance without fabricating data or violating invariants is:

1. **Direct NOT NULL Alteration**: Because there are zero existing leads in the database, the new columns can be added directly as `NOT NULL` (for `target_entity_id`) without needing a multi-step backfill process.
2. **Composite FK for Case Consistency**: Add a `UNIQUE(hypothesis_id, case_id)` constraint to `civix.hypothesis` and use a composite foreign key on `civix.investigative_lead(hypothesis_id, case_id)` to guarantee cross-case consistency entirely at the DB level.
3. **Outbox Payload Update**: Replace the `investigative_lead` block in `civix.trg_upsert_epistemic_and_edge_outbox()` to emit `target_entity_id` and `hypothesis_id`.
4. **Synchronized Application Release**: The database migration (`020_adr026_investigative_lead.sql`) must be deployed simultaneously with an update to `civix_api/services/neo4j_projection.py` to process the new payload into graph edges, and a rewrite of `civix_api/routers/leads.py` to persist XGBoost outputs rather than returning ephemeral results.
