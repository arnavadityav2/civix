# NEO4J PROJECTION AUDIT

## 1. Projection Rules
PostgreSQL is the source of truth. Neo4j is a materialized view.

## 2. Second-Order Finding: Tombstone Propagation [HIGH]
When a bitemporal row's `tx_end` is closed in PostgreSQL, the Neo4j edge MUST be removed or marked inactive.
**Resolution**: The Outbox pattern (ADR-008) must emit a `DEACTIVATE_EDGE` event when `tx_end` is mutated by the append-only trigger.

**Verdict**: PASS with Outbox enhancement.\n