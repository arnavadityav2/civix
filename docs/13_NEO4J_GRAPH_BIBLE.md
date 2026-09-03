# 13 — Neo4j Graph Bible
**Version**: 1.1 | **Date**: 2026-08-29 | **Status**: BLK-04 RESOLVED (ADR-015) — HAS_STANCE replaces SUPPORTS/CONTRADICTS

---

## 1. Neo4j Role

Neo4j is an **analytical projection** of the PostgreSQL system of record.

- PostgreSQL → Neo4j (one direction only, via outbox)
- Neo4j is reconstructable from PostgreSQL at any time
- Neo4j may be stale by up to [STATUS: OPEN DECISION — acceptable lag TBD]
- No application code writes directly to Neo4j (ADR-008)

---

## 2. Synchronization (Outbox Pattern)

```
PostgreSQL write (entity upserted/modified)
  → trigger writes to civix.outbox
  → CDC consumer polls outbox
  → CDC consumer issues Neo4j Cypher (MERGE / SET / DETACH DELETE)
  → outbox.consumed_at set
```

**Tombstone flow** (for expunged records):
```
legal_restriction(EXPUNGED) created in PostgreSQL
  → trigger writes outbox(action=TOMBSTONE, entity_id=X)
  → CDC consumer: MATCH (n {entity_id: X}) DETACH DELETE n
  → All relationships of X are also deleted (DETACH)
  → Dependent hypotheses/leads flagged for re-evaluation
```

---

## 3. Node Types

| Label | Source Table | Properties | Excluded When |
|---|---|---|---|
| `:Person` | `civix.person` | entity_id, display_name, is_deceased | EXPUNGED |
| `:SourceIdentity` | `civix.source_identity` | entity_id, raw_identifier, identifier_type | EXPUNGED |
| `:Vehicle` | `civix.vehicle` | entity_id, registration_number, vehicle_type | EXPUNGED |
| `:PhoneNumber` | `civix.phone_number` | entity_id, msisdn | EXPUNGED |
| `:Device` | `civix.device` | entity_id, imei, device_type | EXPUNGED |
| `:Account` | `civix.financial_account` | entity_id, masked_number, account_type | EXPUNGED |
| `:Property` | `civix.property` | entity_id, property_ref, property_type | EXPUNGED |
| `:Organization` | `civix.organization` | entity_id, legal_name, org_type | EXPUNGED |
| `:Network` | `civix.network` | entity_id, network_name | EXPUNGED |
| `:Location` | `civix.location` | entity_id, location_name, location_type | Never excluded |
| `:Event` | `civix.event` | event_id, event_type, occurred_at_lower, occurred_at_upper | Never excluded |
| `:Assertion` | `civix.assertion` | assertion_id, predicate, epistemic_status | `epistemic_status=REFUTED` |
| `:Hypothesis` | `civix.hypothesis` | hypothesis_id, status | `status=ARCHIVED` |
| `:Lead` | `civix.investigative_lead` | lead_id, case_id, priority, status | `status IN ('CLOSED', 'FALSE_POSITIVE')` |

**NOT projected**: `source_record`, `evidence_artifact`, `evidence_instance`, `observation`, `extraction`, `audit_event`, `legal_restriction`, `provenance`, `data_quality_issue`, `scenario.ground_truth`, any row with `generation_run_id IS NOT NULL`

---

## 4. Relationship Types

| Cypher Relationship | From | To | Properties | Algorithm Safety |
|---|---|---|---|---|
| `[:PARTICIPATED_AS {role}]` | Entity node | `:Event` | participant_role, role_confidence | ✅ Safe |
| `[:ASSERTS]` | `:Assertion` | Entity node (object) | predicate, epistemic_status | ✅ Safe |
| `[:ASSERTED_BY]` | Entity node (subject) | `:Assertion` | predicate | ✅ Safe |
| `[:HAS_STANCE {stance, weight, tx_start}]` | `:Assertion` | `:Hypothesis` | stance, weight, tx_start | ⚠️ Filter on `stance='SUPPORT'` before any structural algorithm. See ADR-015. |
| `[:RESOLVES_TO]` | `:SourceIdentity` | `:Person` | confidence | ✅ Safe |
| `[:DERIVED_FROM]` | `:Assertion\|:Extraction` | `:Observation\|:Evidence` | method | ✅ Safe — provenance |

> [!IMPORTANT]
> **BLK-04 RESOLUTION (ADR-015, 2026-08-29)**
>
> The former `[:SUPPORTS]` and `[:CONTRADICTS]` relationship types have been REMOVED.
>
> **Reason**: `[:CONTRADICTS]` as a named relationship type is a structural graph edge. Neo4j has no concept of a named relationship type that is non-structural. This contradicts ADR-007 which requires CONTRADICT stance to be a relationship PROPERTY, not a separate graph edge type.
>
> **Replacement**: A single `[:HAS_STANCE]` relationship type carries stance as a property:
> ```
> (:Assertion)-[:HAS_STANCE {
>   stance: 'SUPPORT' | 'CONTRADICT' | 'NEUTRAL' | 'INCONCLUSIVE',
>   weight: float (default 1.0),
>   tx_start: datetime (system time of assignment)
> }]->(:Hypothesis)
> ```
>
> **Algorithm projection rule**: All structural graph algorithms (PageRank, Louvain, shortest path) MUST use a projection that filters `stance = 'SUPPORT'`. See Section 5.

> [!IMPORTANT]
> **ADR-030: Investigative Lead Graph Representation**
>
> The `:Lead` node is strictly projected as a disconnected node. 
> There are NO authorized structural relationships from or to a `:Lead` node (e.g., `[:TARGETS]`, `[:HAS_STANCE]`, `[:GENERATED_FROM]`, `[:SUPPORTS]`).
> Its foreign keys (`target_entity_id`, `hypothesis_id`) remain PostgreSQL-only workflow properties. Leads are filtered by `case_id` for isolation.

---

## 5. Graph Algorithm Safety Rules (ADR-007, ADR-015)

**CRITICAL**: Only `HAS_STANCE` edges with `stance='SUPPORT'` may be included in structural graph algorithm projections. All other stance values are stored in Neo4j but EXCLUDED from traversal.

```cypher
// WRONG — includes all HAS_STANCE edges regardless of stance
CALL gds.pageRank.stream('myGraph') YIELD nodeId, score

// CORRECT — project only SUPPORT relationships
CALL gds.graph.project(
  'investigativeGraph',
  ['Person', 'SourceIdentity', 'Organization', 'Network'],
  {
    PARTICIPATED_AS: { orientation: 'UNDIRECTED' },
    HAS_STANCE: {
      orientation: 'NATURAL',
      properties: ['weight'],
      relationshipFilter: "stance = 'SUPPORT'"
    }
  }
)
// CONTRADICT, NEUTRAL, INCONCLUSIVE are stored in Neo4j but excluded from this projection
// Hypothesis SCORING uses PostgreSQL aggregate (not graph traversal):
// SELECT SUM(CASE WHEN stance='SUPPORT' THEN weight ELSE 0 END) as support_score,
//        SUM(CASE WHEN stance='CONTRADICT' THEN weight ELSE 0 END) as contradict_score
// FROM civix.hypothesis_support WHERE hypothesis_id = $h
```

---

## 6. Temporal Graph Slices

For temporal analysis, filter by event timestamps:
```cypher
// Find all events involving P-01 in August 2026
MATCH (p:Person {entity_id: $person_id})-[:PARTICIPATED_AS]->(e:Event)
WHERE e.occurred_at_lower >= datetime('2026-08-01T00:00:00Z')
  AND e.occurred_at_upper <= datetime('2026-08-31T23:59:59Z')
RETURN e
```

---

## 7. Identity Merge/Split in Neo4j

**Identity merge**:
1. `SourceIdentity` A was confirmed as `Person` P-01
2. `SourceIdentity` B was confirmed as `Person` P-01 (same person as A)
3. Both `:RESOLVES_TO` relationships point to `:Person` P-01
4. Historical event participations remain on the `:SourceIdentity` nodes
5. Graph traversal from `:Person` P-01 can reach all events via both source identities

**Identity split**:
1. `SourceIdentity` B is now known to be `Person` P-99 (different from P-01)
2. Outbox emits: update `SourceIdentity` B's `[:RESOLVES_TO]` to point to P-99 (new node)
3. Historical events on `:SourceIdentity` B are now correctly attributed to P-99
4. No event records are modified — just the resolution edge

**Rejected Resolution (ADR-031)**:
1. `REJECTED` identity resolutions are NOT represented by any Neo4j relationship.
2. The CDC projection MUST gracefully ignore a rejected resolution.
3. No negative relationship (e.g., `REJECTS` or `NOT_RESOLVES_TO`) is authorized.

---

## 8. Cross-Case Access Filtering

Graph queries must respect case access:
```cypher
// A user should only see hypotheses from their authorized cases
MATCH (h:Hypothesis)
WHERE h.case_id IN $authorized_case_ids
RETURN h
```

The `$authorized_case_ids` parameter is provided by the backend based on the user's `case_access` records.
