# PHASE 7 STEP 6 REVISION 8 — AGENT B INDEPENDENT AUDIT (FINAL ADVERSARIAL GATE)

## 1. Independent Audit Verdict

> **REJECTED — REVISION REQUIRED**

## 2. Repository Evidence
- **PostgreSQL (`database/migrations/005_identity_resolution.sql`, `008_epistemic_pipeline.sql`):** Verified `identity_resolution` relies on `superseded_by` to tombstone edges, and `assertion`/`hypothesis_support` rely on `tx_end`. Historical edges are preserved, not physically deleted.
- **Neo4j Query Layer (`civix_api/services/neo4j_query.py:L25-31`):** Verified that `get_case_graph` uses a hardcoded `(NOT node:Case AND NOT node:FIR)` path filter and performs ZERO relationship-level property filtering (`-[*0..{depth}]-`).

## 3. Security Findings
- **Graph Bleed:** **BLOCKER** — See Blocker-01.
- **Assertion Authorization:** **BLOCKER** — See Blocker-01.
- **Event Global Visibility:** **PASS**
- **Visibility Status:** **BLOCKER** — See Blocker-01.
- **Label Injection:** **PASS**
- **Payload Integrity:** **PASS**

## 4. PostgreSQL / RLS Findings
- PostgreSQL RLS correctly governs `authorized_case_ids` and `case_id`.

## 5. Outbox / Trigger Findings
- `tx_end` and `superseded_by` correctly configured in trigger scopes.

## 6. CDC / Concurrency Findings
- Stale event and endpoint races natively resolved by Revision 8 Cypher strategy.

## 7. Neo4j Schema Findings
- Valid constraints.

## 8. Cypher Correctness Findings
- Assertion insertion order correctly fixed.

## 9. Assertion Cardinality Findings
- Deletion loop enforces 1:1 active mapping properly.

## 10. Lifecycle Findings
- **Lifecycle Edge Bleed:** **BLOCKER** — See Blocker-02.

## 11. Polymorphic Identity Findings
- Verified `civix.entity_type_enum`.

## 12. Testing Findings
- Requires tests for superseded edge exclusion.

## 13. Live Neo4j Findings
- Not executed.

## 14. Attack Matrix

| Attack                        | Expected Defense  | Actual Defense | Result |
| ----------------------------- | ----------------- | -------------- | ------ |
| Case A → Hypothesis B         | ACL               | Hardcoded Case/FIR rules | FAIL (Bleed) |
| Case A → Lead B               | ACL               | Hardcoded Case/FIR rules | FAIL (Bleed) |
| Case A → Assertion B          | ACL               | Hardcoded Case/FIR rules | FAIL (Bleed) |
| Superseded Identity Traversal | Edge filter       | Unfiltered traversal | FAIL (Topology bleed) |
| Retracted Assertion Traversal | Edge filter       | Unfiltered traversal | FAIL (Topology bleed) |

## 15. Blocking Defects

### BLOCKER-01 — Catastrophic Step 5 Graph Bleed
**Severity:** CRITICAL
**Evidence:** `civix_api/services/neo4j_query.py:L25-31`
**Why unsafe:** Revision 8's plan assumes that property-driven ACLs (`visibility_status`, `authorized_case_ids`) will protect the new nodes. However, `neo4j_query.py` in the repository currently uses hardcoded label logic: `WHERE all(node IN nodes(path) WHERE (NOT node:Case AND NOT node:FIR)...)`. If Step 6 is implemented without explicitly rewriting the `get_case_graph` Cypher, `Assertion`, `Hypothesis`, and `Lead` will be evaluated as "Not Case/FIR" and will be fully exposed to global traversal, completely bypassing Case isolation.
**Required correction:** The plan MUST explicitly provide the exact Cypher required to rewrite `neo4j_query.py` to enforce the property-based ACL (`coalesce(node.visibility_status, 'ACTIVE') = 'ACTIVE'`, etc.) on all nodes in the path.

### BLOCKER-02 — Historical / Superseded Edge Bleed
**Severity:** HIGH
**Evidence:** `civix_api/services/neo4j_query.py` and `database/migrations/005_identity_resolution.sql`
**Why unsafe:** The CDC projection correctly populates `tx_end` and `superseded_by` on edges in Neo4j to preserve historical audit trails without physical deletion. However, the generic traversal query in `neo4j_query.py` (`-[*0..{depth}]-`) performs ZERO filtering on relationships. This will cause live traversals to cross logically deactivated edges, allowing cases to bleed into superseded identities or retracted assertions.
**Required correction:** The path evaluation in `neo4j_query.py` MUST be updated to explicitly mandate `all(rel IN relationships(path) WHERE rel.tx_end IS NULL AND rel.superseded_by IS NULL)`.

## 16. Non-Blocking Findings
None.

## 17. Required Corrections
1. Provide the complete, explicit Cypher query update for `civix_api/services/neo4j_query.py` to replace the hardcoded label ACL with the property-based node ACL.
2. Add explicit relationship lifecycle filtering (`tx_end IS NULL` and `superseded_by IS NULL`) to the same traversal query.

## 18. Regression Assessment
If implemented without the query patch, Revision 8 would trigger a massive security regression by exposing all Phase 7 nodes to global access.

## 19. Forbidden File Assessment
N/A (Plan Only).

## 20. Final Governance Decision

> **STEP 6 REVISION 8 REJECTED — IMPLEMENTATION NOT AUTHORIZED.**
