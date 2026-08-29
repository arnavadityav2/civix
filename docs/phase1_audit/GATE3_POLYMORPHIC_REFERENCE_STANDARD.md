# GATE 3: POLYMORPHIC REFERENCE STANDARD
Date: 2026-08-29

## Rules
- `civix.entity` is the absolute supertype.
- `BEFORE DELETE` trigger on `civix.entity` executes `RAISE EXCEPTION 'Physical deletion of entities is prohibited.'`.
- Orphan prevention is 100% guaranteed by PostgreSQL FK constraints to `civix.entity(entity_id)`.\n