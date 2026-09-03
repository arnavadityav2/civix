# CIVIX PROJECT MASTER RELEASE AUDIT

## 1. Executive Verdict
**FRONTEND GO WITH P0 CONDITIONS**

The repository is fundamentally sound in its architecture and API implementation. civix_api handles complex domain operations with robust RLS case isolation, identity resolution, and relationship extraction. 
However, two P0 database-level integrity flaws were discovered:
1. **F-01 Null Idempotency:** The ingestion uniquely allows duplicate source_records if external_reference is NULL.
2. **F-02 Entity Immutability:** civix.entity lacks the physical delete block present on all other core tables.

These P0 fixes are straightforward SQL trigger/index updates and must be applied before the frontend connects to ingestion.

## 2. Repository Reality
*   **Backend:** Fully implemented FastAPI application (civix_api) with 87 passing tests.
*   **Frontend:** Does not exist yet.
*   **ML:** Offline analytical baselines exist (civix_ml/models/baselines.py), but no inference API is implemented.
*   **NLP:** Does not exist yet.
*   **Graph (Neo4j):** Projections are coded but CDC worker is currently inactive.
*   **Database:** Advanced schema with RLS and trigger-based provenance is live.

## 3. Governance Reconciliation
docs/00_CIVIX_CURRENT_STATE.md is significantly stale and falsely claims ADR-026 is blocked. The repository code and database catalog are the definitive source of truth.

## 4. ADR Status Matrix
| Concept | Claimed State | Actual State | Conflict |
|---------|--------------|-------------|----------|
| ADR-026 | Blocked | Complete | YES |
| ADR-029 | Complete | Complete | NO |
| ADR-033 | Complete | Partial (Missing Trigger) | YES |
| ADR-034 | Complete | Complete | NO |
| ADR-035 | Hardened | Flawed (NULL bypass) | YES |
| GNN | Deferred | Frozen | NO |

## 5. Database Verification
*   civix.investigative_lead contains required columns (	arget_entity_id, hypothesis_id).
*   civix.entity has isibility_status for tombstoning, but lacks the enforce_no_delete physical trigger.

## 6. Security / RLS Verification
*   **Safe.** civix.entity intentionally lacks RLS (ADR-029). APIs (like search.py:64) successfully enforce isolation using application-level cross-joins to case_entity_role.

## 7. Authentication Verification
*   JWT authentication (civix_api/auth) is fully implemented. Secret rotation and set_config transaction-local context switching is secure.

## 8. Provenance Verification
*   Append-only triggers exist on civix.provenance and source_record.

## 9. Ingestion Verification (F-01)
*   **Vulnerable.** An adversarial script firing 50 concurrent INSERT queries with external_reference = NULL successfully created 50 duplicate records because the unique index WHERE external_reference IS NOT NULL ignored them.

## 10. API Verification
*   All endpoints for Cases, Entities, Leads, Hypotheses, Identity Resolution, and Search are present and actively tested.

## 11. Test Verification
*   pytest tests/api/ -v ? 87 passed, 1 skipped. 
*   Test isolation is clean (transactions rollback after each run).

## 12. ML Reality Check (Level 1)
*   Models (Isolation Forest, XGBoost) are Level 1 (Trainable offline models). No API integration exists. GNN is strictly deferred.

## 13. NLP Reality Check (Level 0)
*   No NLP extraction code exists in the repository.

## 14. Neo4j / CDC Reality Check (Level 1)
*   PostgreSQL outbox triggers exist. 
eo4j_projection.py exists. The worker daemon itself is not actively running.

## 15. Frontend Readiness
*   **Ready.** The API is secure and stable. The frontend can be built immediately for Dashboard, Search, and Profiles. Ingestion UI must wait for F-01 patch.

## 16. Real-World Data Readiness
*   **Partial.** Schema handles real-world entities, but ingestion only accepts strict JSON schemas. CSV/PDF adapters are missing.

## 17. PS Relevance Matrix
| Requirement | Capability | Evidence | Gap | Priority |
|-------------|------------|----------|-----|----------|
| Entity Extraction | Resolution API | identity.py | No NLP | P2 |
| Graph Discovery | Outbox/Projections | 
eo4j_projection.py | No UI/CDC | P1 |
| AI/ML | Offline Baselines | aselines.py | No Inference API | P2 |

## 18. Findings Register
| ID | Severity | Finding | Impact | Fix | Blocks |
|----|----------|---------|--------|-----|--------|
| F-01 | CRITICAL | NULL Idempotency Bypass | Duplicate graphs | Use COALESCE in Index | Ingestion UI |
| F-02 | HIGH | Entity Deletion Vulnerability | Broken Provenance | Attach existing trigger | No |

## 19-25. Execution Roadmap & Next Actions
*(See implementation_plan.md for exact steps and sequence).*

