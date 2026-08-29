# POLYMORPHIC REFERENCE STANDARD

## 1. The Challenge
CIVIX relies heavily on polymorphic relationships:
- `event_participant.entity_id`
- `case_entity_role.entity_id`
- `financial_account_role.entity_id`

## 2. CIVIX Standard Resolution (ADR-001 Validation)
CIVIX solves polymorphism via a **Supertype/Subtype** architecture (ADR-001).
- **Supertype**: `civix.entity` (UUID PK, entity_type ENUM)
- **Subtypes**: `civix.person`, `civix.vehicle`, etc. (UUID PK/FK to entity)

### 3. Second-Order Finding: Subtype Orphan Risk [CRITICAL]
If a user deletes a `person`, the `entity` row might remain if not cascaded, leaving dangling `event_participant` references.
**Resolution**: `ON DELETE CASCADE` from subtype to supertype is FORBIDDEN due to audit requirements. Instead, CIVIX uses **Tombstoning**:
- `entity.visibility_status` = 'EXPUNGED'
- No physical DELETE is allowed on `civix.entity`.

**Verdict**: PASS with Tombstone enforcement.\n