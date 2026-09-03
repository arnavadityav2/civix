# PHASE 7 STEP 7 — IMPLEMENTATION PLAN

## 1. Objective
Produce a strict, repository-grounded implementation plan for Phase 7 Step 7 while verifying the handoff state of Phase 7 Step 6, without committing any code modifications or prematurely advancing the governance gate.

## 2. Repository Evidence
An exhaustive search was conducted across all Phase 7 planning artifacts, execution histories, the `docs/` directory, and specifically `19_IMPLEMENTATION_MASTER_PLAN.md`.

* `19_IMPLEMENTATION_MASTER_PLAN.md` defines Phase 7 strictly as "Neo4j Projection", with objectives scoped to CDC consumer implementation and Cypher upserts. 
* There are no outstanding architectural specifications or ADRs defining a "Step 7".
* The documented scope of Phase 7 (Neo4j Projection) has been structurally completed up through Step 6.

## 3. Step 6 Handoff Status
Phase 7 Step 6 completed the construction of the Neo4j Projection Pipeline for the Epistemic model. 20/20 PostgreSQL/Neo4j mock-integrated integration tests passed. However, it remains gated:

> **IMPLEMENTATION COMPLETE — ACCEPTANCE BLOCKED**

**Missing Handoff Requirement:** Step 6 requires a formal **Live Neo4j Verification** (testing missing endpoint rollbacks, stale event rejection, Assertion cardinality duplication collapse, graph bleed traversal boundaries, lifecycle filtering, and replay idempotency on a live DB). This has not been performed. Step 7 cannot bypass this gate.

## 4. Step 7 Scope

> **STEP 7 SCOPE NOT ESTABLISHED FROM REPOSITORY EVIDENCE**

There is no repository evidence defining the architectural problem, purpose, or intended deliverables for Phase 7 Step 7. Any proposed implementation at this stage would be an invention.

## 5. Architecture
*N/A — Scope not established.*

## 6. Database Changes
*N/A — Scope not established.*

## 7. Neo4j Changes
*N/A — Scope not established.*

## 8. API Changes
*N/A — Scope not established.*

## 9. CDC Implications
*N/A — Scope not established.*

## 10. Security Model
*N/A — Scope not established.*

## 11. Threat Model
*N/A — Scope not established.*

## 12. Concurrency Model
*N/A — Scope not established.*

## 13. Failure Classification
*N/A — Scope not established.*

## 14. Migration Strategy
*N/A — Scope not established.*

## 15. File Scope
*N/A — Scope not established.*

## 16. Forbidden Files
The following files remain strictly forbidden from modification without explicit authorization:
* `civix_api/worker/cdc.py`
* All existing schema migrations (`database/migrations/*.sql`)
* `civix_api/services/neo4j_projection.py` (unless explicitly requested to remediate Step 6 topology drift)
* `civix_api/services/neo4j_query.py` 
* All RLS policy files

## 17. Test Matrix
*N/A — Scope not established.*

## 18. Adversarial Attack Matrix
### Step 6 Handoff Validation (Topology Drift Analysis)
A formal inspection of `civix_api/services/neo4j_projection.py` reveals the following **TOPOLOGY DRIFT** between the Step 6 Revision 10 approved plan and the actual implementation:

| Edge Concept | Approved Revision 10 Topology | Actual Implemented Topology (`neo4j_projection.py`) | Status |
| :--- | :--- | :--- | :--- |
| **Event Participant** | `(:Event)-[:PARTICIPATED_IN]->(:Entity)` | `(:Event)-[:PARTICIPATED_AS]->(:Entity)` | **DRIFT** |
| **Hypothesis Support** | `(:Assertion)-[:SUPPORTS/REFUTES]->(:Hypothesis)` | `(:Assertion)-[:HAS_STANCE]->(:Hypothesis)` | **DRIFT** |
| **Identity Resolution** | `(:SourceIdentity)-[:RESOLVED_TO]->(:Person)` | `(:Identity)-[:RESOLVES_TO]->(:Person)` | **DRIFT** |
| **Assertion Subject** | `(:SourceIdentity)-[:ASSERTED_BY]->(:Assertion)` | `(:Assertion)-[:ASSERTED_BY]->(:Identity)` | **DRIFT (Direction + Label)** |
| **Assertion Object** | `(:Assertion)-[:ASSERTS]->(:Person)` | `(:Assertion)-[:ASSERTS]->(:Entity)` | OK (Generic Target) |

> [!WARNING]
> **TOPOLOGY DRIFT DETECTED**: The implementation agent significantly altered relationship names, target labels, and edge directions without explicit ADR authorization. For example, the `ASSERTED_BY` edge points *away* from the Assertion in the code (`CREATE (a)-[:ASSERTED_BY]->(i)`), directly contradicting the approved inbound model. This drift must be remediated or explicitly accepted before Step 6 can pass Live Neo4j Verification.

## 19. Deployment Sequence
*N/A — Scope not established.*

## 20. Acceptance Criteria
*N/A — Scope not established.*

## 21. Risks
Proceeding with any "Step 7" development violates the Phase 7 master plan and introduces severe risk of orphaned architecture, particularly given the confirmed Topology Drift in Step 6.

## 22. Governance Decision

### IMPLEMENTATION BLOCKED

**Blocker 1**: Phase 7 Step 7 lacks any defined scope in the repository documentation.
**Blocker 2**: Phase 7 Step 6 requires remediation of explicit **TOPOLOGY DRIFT** in Neo4j edge directions and labels.
**Blocker 3**: Phase 7 Step 6 is pending mandatory **Live Neo4j Verification** tests.

Step 7 cannot proceed until Step 6 is verified, remediated, and accepted, and a formal architectural directive for Step 7 is supplied.
