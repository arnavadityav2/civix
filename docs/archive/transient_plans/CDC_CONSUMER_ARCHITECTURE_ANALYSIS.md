# CDC CONSUMER ARCHITECTURE DECISION ANALYSIS

## 1. Executive Summary
The CIVIX project requires a Change Data Capture (CDC) consumer to project data from PostgreSQL into Neo4j (Phase 7). Per architecture invariant INV-20 and ADR-008, all Neo4j writes must occur via a transactional outbox (`civix.outbox`) rather than direct application writes. The open decision is selecting the technology to transport and consume these outbox events. The candidates are Kafka, Redis Streams, and PostgreSQL `pg_notify` (with polling fallback). This analysis evaluates these candidates against the repository's verified constraints to produce a formal recommendation.

## 2. Changes Since Independent Audit
Following the independent governance audit (Agent B), this architecture analysis and ADR-026 have been revised to address three material architectural flaws in the original proposal:
1. **Per-Entity Ordering**: The original reliance on `SKIP LOCKED` failed to guarantee chronological ordering for concurrent workers. This is resolved by mandating PostgreSQL advisory locks keyed by `entity_id`.
2. **Replay Safety**: The original claim that nulling `consumed_at` trivially handled replay was rejected. This is resolved by mandating strict Cypher version checks (`last_updated`) to prevent stale overwrites.
3. **Worker Lifecycle**: The ambiguity of running the worker inside FastAPI was rejected. This is resolved by mandating a dedicated, standalone worker process.

## 3. Verified Current Architecture
The following facts are verified from the repository:
* **Outbox Schema**: `civix.outbox` exists (Migration 009). It contains `id`, `entity_id`, `action`, `entity_type`, `payload` (JSONB), `created_at`, and `consumed_at`.
* **Triggers**: PostgreSQL triggers are already implemented (Migration 011) to populate the outbox atomically with state changes (e.g., entity tombstoning, hypothesis support).
* **Neo4j Stance**: INV-09 states PostgreSQL is authoritative; Neo4j is derived. INV-20 mandates the outbox as the ONLY mechanism for Neo4j synchronization.
* **Tech Stack**: The backend relies on FastAPI and SQLAlchemy AsyncSession (ADR-023, ADR-024).
* **Current Stage**: The project is aiming for the SIH 2026 demo (Phase 14) using Golden World v2.1 synthetic data.
* **Security**: RLS is enforced at the PostgreSQL layer. The outbox payload contains the raw serialized data necessary for graph projection.

## 4. Requirements
Derived from the CIVIX architecture and invariants:
* **Strict Adherence to INV-20**: The consumer must read from the existing `civix.outbox` table.
* **Durability and Delivery Guarantees**: Events must not be lost if the consumer crashes.
* **Idempotency and Replayability**: Replaying historical events must be safe and must not corrupt newer graph state with stale data.
* **Per-Entity Ordering**: Events for a given entity must be processed in strict chronological order to prevent out-of-sequence mutations.
* **Operational Simplicity**: The solution must fit the SIH 2026 demo constraints without introducing massive architectural debt, unwarranted infrastructure bloat, or excessive memory requirements.

## 5. Candidate Analysis

### Candidate 1: Kafka
* **Advantages**: Massive scalability, strong ordering guarantees per partition (by entity key), robust ecosystem (e.g., Debezium), and excellent replayability.
* **Disadvantages**: Heavy infrastructure footprint (requires JVM, Zookeeper or KRaft). Massive overkill for the current investigative case management volume and demo stage. Requires standing up an entire external cluster, significantly complicating the local development and deployment topology.
* **Compatibility**: Poor fit for the current SIH 2026 demo stage due to extreme operational overhead.

### Candidate 2: Redis Streams
* **Advantages**: Lightweight pub/sub with persistence and consumer groups. Faster than database polling.
* **Disadvantages**: Introduces a new infrastructure dependency. Requires either a dual-write mechanism (which breaks atomic transactions) or a dedicated PostgreSQL-to-Redis connector to move the `civix.outbox` rows into Redis reliably.
* **Compatibility**: Moderate fit. Adds a moving part that complicates the deployment architecture without providing enough benefit over the existing database queue.

### Candidate 3: PostgreSQL `pg_notify` (with Outbox Polling Fallback)
* **Advantages**: Zero additional infrastructure. Uses the *existing* `civix.outbox` table as the durable queue. `pg_notify` acts as a low-latency wakeup signal to an asyncio Python worker, which then processes rows using `SELECT ... FOR UPDATE SKIP LOCKED`. Fits perfectly within the existing FastAPI/SQLAlchemy AsyncSession stack.
* **Disadvantages**: PostgreSQL `pg_notify` has an 8000-byte payload limit. However, this is mitigated by sending only a wakeup signal (e.g., "new_outbox_event") and letting the worker pull the full JSONB payload directly from the table. Polling can bottleneck at massive scale (millions of rows/sec), but is easily sufficient for the SIH demo and standard investigative loads.
* **Compatibility**: Excellent fit. Leverages the work already completed in Phase 2A/Phase 3.

## 6. Decision Matrix

| Criterion | Kafka | Redis Streams | pg_notify + outbox |
| :--- | :---: | :---: | :---: |
| **Existing architecture fit** | 1 | 2 | 3 |
| **Delivery guarantees** | 3 | 2 | 3 |
| **Replay capability** | 3 | 2 | 3 (With Cypher checks) |
| **Ordering** | 3 | 2 | 3 (With Advisory Locks) |
| **Failure recovery** | 3 | 2 | 3 |
| **Operational complexity** | 1 | 2 | 3 |
| **Scaling** | 3 | 3 | 2 |
| **Security/RLS compatibility**| 2 | 2 | 3 |
| **Current-project suitability**| 1 | 2 | 3 |

*(Score: 1 = Poor, 2 = Acceptable, 3 = Excellent. `pg_notify + outbox` scores highest due to zero infrastructural overhead and perfect alignment with existing migrations.)*

## 7. Failure/Recovery Analysis
* **Consumer crash**: The worker dies before executing `UPDATE civix.outbox SET consumed_at = NOW()`. The event remains unconsumed. Upon restart, the worker queries `WHERE consumed_at IS NULL` and resumes processing without data loss.
* **PostgreSQL outage**: The entire system safely halts. The outbox data persists on disk.
* **Neo4j outage**: The consumer catches the connection exception, backs off, and does NOT update `consumed_at`. Events queue safely in `civix.outbox` until Neo4j is restored.
* **Concurrent workers**: Multiple workers can safely coexist without violating per-entity ordering by using PostgreSQL advisory locks keyed on the `entity_id`. If Worker B fetches Event 2 for Entity X while Worker A is processing Event 1, the advisory lock ensures Worker B cannot process Event 2 out of order.
* **Replay stale event**: Intentional or accidental replay of older events will be safely ignored by Neo4j because projection queries enforce timestamp version checks (e.g., rejecting writes where the new event timestamp is older than the graph node's `last_updated` property).

## 8. Recommendation
**Recommended Candidate:** PostgreSQL `pg_notify` combined with Asyncio Outbox Polling, augmented by Advisory Locks and Cypher versioning.

**Supporting Evidence:** The repository explicitly defines `civix.outbox` with a `consumed_at` column in Migration 009. PostgreSQL is the authoritative source (INV-09). Using the database queue avoids heavy external dependencies like Kafka or Redis, perfectly serving the SIH 2026 demo requirements while providing strong safety guarantees through transaction locking and idempotency.

## 9. ADR Draft

---
### ADR-026: Neo4j CDC Consumer Architecture (PROPOSED — REVISION 2)

**Date**: 2026-08-31
**Status**: PROPOSED

**Context**
Phase 7 (Neo4j Projection) requires a mechanism to securely and reliably transport authoritative PostgreSQL data into the analytical Neo4j graph. INV-20 mandates this occur exclusively via the `civix.outbox` table to prevent split-brain topology. We must select the technology for the CDC consumer and define its concurrency and replay safety semantics.

**Decision Drivers**
* Zero data loss (Durability).
* Minimal operational overhead for the SIH 2026 demo.
* Strict per-entity chronological ordering (No N+1 events processed before N).
* Replay safety (No stale data overwriting newer graph state).

**Considered Alternatives**
* Kafka / Debezium
* Redis Streams
* PostgreSQL `pg_notify` with `SELECT ... FOR UPDATE SKIP LOCKED` polling

**Recommended Option**
**PostgreSQL `pg_notify` with Outbox Polling, Advisory Locks, and Versioned Graph Projection**. 

1. **Transport**: A dedicated Python asyncio worker will listen to a `pg_notify` channel for wakeup signals. It will fetch events from `civix.outbox` where `consumed_at IS NULL`.
2. **Ordering (Advisory Locks)**: To prevent concurrent consumers from processing an entity's events out of order via `SKIP LOCKED`, the worker MUST acquire a transaction-level PostgreSQL advisory lock hashed on the `entity_id` (`pg_try_advisory_xact_lock`). If the lock cannot be acquired, the worker skips that event, ensuring no two workers concurrently process events for the same entity.
3. **Replay Safety (Version Checks)**: Replay is triggered by setting `consumed_at = NULL`. To prevent stale overwrites, every Phase 7 Cypher query MUST enforce a version check. Nodes/edges in Neo4j will store a `last_updated` property derived from the outbox `created_at` timestamp. Graph mutations are only applied if `event.created_at >= node.last_updated`.
4. **Worker Lifecycle**: The CDC consumer MUST be deployed as a dedicated, standalone worker process/container, independent of the FastAPI/Uvicorn API replicas, to decouple the API scaling lifecycle from the CDC polling loop.

**Consequences**
* **Positive**: Zero new infrastructure components. Highly durable. Safely replays events without data corruption. Safely scales horizontally (multiple workers) without violating per-entity chronological ordering.
* **Negative**: `pg_notify` payload limits mean the worker must perform a secondary SELECT to fetch the actual JSONB payload.

**Rejected Alternatives**
* Kafka: Rejected due to extreme infrastructure overhead and deployment complexity.
* Redis Streams: Rejected as it introduces a new infrastructure dependency.
* Unordered `SKIP LOCKED`: Rejected because it fatally compromises chronological per-entity ordering.

**Migration/Implementation Implications**
* A `pg_notify` trigger must be added to `civix.outbox`. 
* A standalone Python asyncio consumer script must be written.
* All Cypher queries in Phase 7 must implement `last_updated` conditional logic.
---

## 10. Invariants for Phase 7 Implementation
Any future Phase 7 engineering MUST adhere to the following invariants:
1. **Advisory Lock Requirement**: The consumer MUST acquire `pg_try_advisory_xact_lock(hashtext(entity_id::text))` before processing an outbox row.
2. **Versioned Projection Requirement**: Every Neo4j Cypher mutation MUST include a conditional check ensuring `event.created_at >= node.last_updated`.
3. **Dedicated Worker Requirement**: The consumer MUST be a standalone process, not a background task embedded within the API request-handling pool.

## 11. Implementation Boundary
**NO IMPLEMENTATION IS AUTHORIZED BY THIS ANALYSIS.**
This document strictly serves to propose ADR-026 (Revision 2). Code changes for the `pg_notify` trigger, the Python consumer, or Neo4j Cypher queries are strictly prohibited until the Tech Lead / Agent B independently reviews and accepts this PROPOSED ADR.
