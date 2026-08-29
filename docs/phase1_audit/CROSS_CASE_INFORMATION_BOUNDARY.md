# CROSS-CASE INFORMATION BOUNDARY

## 1. The Scenario
Case A and Case B share an Investigative Lead via `case_link`.

## 2. Second-Order Finding: Assertion RLS Leakage [CRITICAL]
BLK-07 proposed enforcing Assertion access via the provenance chain to `evidence_instance`.
**Vulnerability**: PostgreSQL RLS cannot efficiently execute a recursive CTE through `provenance` → `observation` → `evidence_instance` for millions of assertions. This will cause timeout failures or require bypassing RLS.

**Architectural Resolution**: 
Materialize case access on the Assertion.
Add `authorized_case_ids UUID[]` to `civix.assertion`.
When an extraction creates an assertion, the `case_id` of the source evidence is appended.
RLS Policy: `WHERE authorized_case_ids && (SELECT array_agg(case_id) FROM case_access WHERE user_id = current_user)`.

**Verdict**: REQUIRES SCHEMA MODIFICATION.\n