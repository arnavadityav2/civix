# ADR-026 MIGRATION READINESS REPORT

## 1. Executive Verdict
**READY WITH CONDITIONS**

The repository architecture and current migrations support the implementation of ADR-026. However, several conditions (trigger payload updates and cross-table consistency checks) must be included in the migration to ensure safe deployment, and application code must be overhauled to adapt to the persistent lead model.

## 2. Authoritative Requirements
According to `03_DATABASE_SCHEMA_BIBLE.md` and `11_AI_ML_BIBLE.md`:
- `civix.investigative_lead` must include `target_entity_id` and `hypothesis_id`.
- ML-generated recommendations must be persisted to `civix.investigative_lead`, retaining provenance (`generated_by_run_id`).
- Ephemeral API responses without persistence are banned.

## 3. Actual Current Schema
From `database/migrations/009_workflow_and_legal.sql`:
`civix.investigative_lead` has a standard structure with `lead_id`, `case_id`, `generated_by_run_id`, `generated_by_person`, `lead_text`, `priority`, `status`, etc., but lacks any structural link to an entity or a hypothesis.

## 4. Column/FK Analysis
- **`target_entity_id`**: 
  - Type: `UUID`
  - FK Target: `civix.entity(entity_id)`
  - Nullability: `NOT NULL` (A lead must be about an entity).
  - ON DELETE: `RESTRICT`. Note that `civix.entity` has a `BEFORE DELETE` trigger (`trg_entity_no_delete`) preventing physical deletion (INV-16), making this effectively safe.
- **`hypothesis_id`**:
  - Type: `UUID`
  - FK Target: `civix.hypothesis(hypothesis_id)`
  - Nullability: `NULL` (Must be allowed to be NULL because human investigators might create generalized leads not tied to a specific hypothesis, unless strictly enforced by product rules. For ML leads, it should be enforced at the app layer).

## 5. Lead→Entity Analysis
Linking to `civix.entity(entity_id)` is semantically correct. `civix.entity` is the universal supertype (ADR-001). This allows a lead to target a Person, Vehicle, or Account natively without polymorphic FKs.

## 6. Lead→Hypothesis Analysis
Linking to `civix.hypothesis(hypothesis_id)` is structurally correct. However, since a Hypothesis belongs to a Case, and a Lead belongs to a Case, there is a risk of Case ID mismatch (e.g., Lead in Case A pointing to Hypothesis in Case B).
- Condition: The migration must ideally include a constraint or the application layer must strictly enforce that `lead.case_id = hypothesis.case_id`.

## 7. RLS/Security Analysis
`civix.investigative_lead` is already protected by `policy_lead_select` in `013_rls.sql` which enforces case isolation via `case_id = ANY(civix.get_accessible_case_ids())`. 
Adding `target_entity_id` and `hypothesis_id` does NOT leak data across RLS boundaries because the lead itself remains strictly case-isolated. No new RLS policies are required.

## 8. Bitemporal/Audit Analysis
- **Audit**: `investigative_lead` actions (like status changes) are logged to `civix.audit_event` via application code. No DB trigger changes needed for audit.
- **Outbox/Graph Trigger Impact (CRITICAL)**: `019_outbox_epistemic_and_edge_triggers.sql` contains `trg_upsert_epistemic_and_edge_outbox()`. It constructs a JSON payload for Neo4j when `TG_TABLE_NAME = 'investigative_lead'`.
  - Condition: The outbox trigger MUST be updated in this migration to include `target_entity_id` and `hypothesis_id` in the `v_payload` so the Neo4j CDC consumer can build the correct graph edges.

## 9. Provenance Analysis
The `generated_by_run_id` column already provides the link to `civix.analysis_run`. Adding `target_entity_id` and `hypothesis_id` completes the epistemic chain. No further provenance gaps exist.

## 10. ML/API Compatibility
Inspection of `civix_api/routers/leads.py` reveals:
- The current implementation is fully ephemeral. It extracts candidates, runs XGBoost, and returns a JSON array of `leads`.
- It does NOT persist leads.
- It does NOT use a `hypothesis_id` to contextualize the ML generation.
- **Impact**: The API route must be heavily rewritten AFTER the migration to accept a `hypothesis_id`, persist the XGBoost outputs to `civix.investigative_lead`, and return the persisted objects.

## 11. Existing Data/Backfill Analysis
The Master Plan indicates Phase 5 synthetic data ingestion is complete. This includes the "Rekha Verma" lead. 
Since `target_entity_id` is required (NOT NULL), a direct `ALTER TABLE ADD COLUMN` will fail if there are existing rows.
- Strategy: Add columns as `NULL`, perform a backfill for existing synthetic leads (or truncate and re-run ingestion), then `ALTER TABLE ... SET NOT NULL`.

## 12. Index Analysis
- REQUIRED: `CREATE INDEX idx_lead_target_entity ON civix.investigative_lead(target_entity_id);` (Required for fast traversal of all leads for a given entity).
- REQUIRED: `CREATE INDEX idx_lead_hypothesis ON civix.investigative_lead(hypothesis_id);` (Required for fast retrieval of leads supporting a hypothesis).

## 13. Migration Ordering
The migration should be sequentially numbered after the outbox triggers. Given `019_outbox_epistemic_and_edge_triggers.sql`, this migration should be `020_adr026_investigative_lead.sql`.

## 14. Rollback Analysis
The migration is safely reversible via `ALTER TABLE DROP COLUMN`. Dropping the columns will destroy the graph linkage for any leads created while the migration was active, making rollback destructive to application state once adopted.

## 15. Required Tests
Before ADR-026 is verified, tests must exist for:
- FK constraints (cannot insert lead for non-existent entity/hypothesis).
- Case ID consistency (cannot link lead in Case A to hypothesis in Case B).
- Outbox payload verification (ensure trigger emits `target_entity_id` in JSON).

## 16. Exact Proposed Migration Specification

```sql
-- Migration: 020_adr026_investigative_lead.sql
-- Intent: Implement ADR-026 by linking leads to entities and hypotheses.

SET search_path TO civix, public;

-- 1. Add columns (Nullable initially for safe migration)
ALTER TABLE civix.investigative_lead
ADD COLUMN target_entity_id UUID REFERENCES civix.entity(entity_id) ON DELETE RESTRICT,
ADD COLUMN hypothesis_id UUID REFERENCES civix.hypothesis(hypothesis_id) ON DELETE RESTRICT;

-- 2. Data Backfill (If applicable for existing synthetic leads)
-- UPDATE civix.investigative_lead SET target_entity_id = <fallback_uuid> WHERE target_entity_id IS NULL;

-- 3. Enforce NOT NULL on target_entity_id
ALTER TABLE civix.investigative_lead
ALTER COLUMN target_entity_id SET NOT NULL;

-- 4. Create Indexes
CREATE INDEX idx_lead_target_entity ON civix.investigative_lead(target_entity_id);
CREATE INDEX idx_lead_hypothesis ON civix.investigative_lead(hypothesis_id);

-- 5. Update Outbox Trigger (Critical Condition)
CREATE OR REPLACE FUNCTION civix.trg_upsert_epistemic_and_edge_outbox()
RETURNS TRIGGER LANGUAGE plpgsql SECURITY INVOKER AS $$
-- ... (existing logic) ...
    ELSIF TG_TABLE_NAME = 'investigative_lead' THEN
        v_entity_id := NEW.lead_id;
        v_entity_type := 'investigative_lead';
        v_payload := jsonb_build_object(
            'lead_id', NEW.lead_id,
            'case_id', NEW.case_id,
            'target_entity_id', NEW.target_entity_id,
            'hypothesis_id', NEW.hypothesis_id,
            'lead_text', NEW.lead_text,
            'priority', NEW.priority,
            'status', NEW.status
        );
-- ... (existing logic) ...
$$;
```

## 17. Remaining Risks
- The application layer currently lacks a mechanism to enforce `lead.case_id = hypothesis.case_id`.
- Rewriting `civix_api/routers/leads.py` is mandatory, as it fundamentally violates ADR-026's ban on ephemeral ML leads.

## 18. Final Readiness Verdict
**READY WITH CONDITIONS** (Update Outbox Trigger, Handle Data Backfill, Update API Route).
