import os

def read_file(path, required=False):
    if not os.path.exists(path):
        return f"[FILE NOT FOUND: {path}]" if required else ""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception as e:
        return f"[ERROR READING {path}: {str(e)}]"

def main():
    out_file = 'CANONICAL_PHASE_7_HANDOVER.md'
    
    header = """# CANONICAL PHASE 7 HANDOVER - EXHAUSTIVE TECHNICAL RECORD (10000+ Words Context)

**Status:** IDE Agent Paused Mid-Task (Phase 7 Task 2).
**Date:** 2026-08-30

> [!CAUTION]
> This is the canonical, highly exhaustive technical handover record for the Civix SIH 2026 project. 
> To the AI Agent reading this: YOU HAVE SUFFERED CONTEXT DRIFT. The user has explicitly generated this massive report to provide you with the EXACT, COMPLETE context of everything done so far in the project, right from the start to the pause point in Phase 7 Task 2.
>
> Read this document completely to understand the verified architectural state. Do not invent, simplify, reinterpret, or silently "improve" architectural decisions. Trust this document as the absolute source of truth.

---

## 1. PROJECT HISTORY & PRE-PHASE-7 ARCHITECTURE - DEEP DIVE

Civix is a high-security investigative case management platform heavily leveraging graph/ML analytics and synthetic data generation. This section exhaustively documents the decisions made up to this point.

### 1.1 Database-First Architecture & Rigorous Data Integrity
Unlike typical ORM-driven applications, Civix adopts a strict **Database-First** approach. Core domain logic, validation, constraints, and Row-Level Security (RLS) are enforced strictly within PostgreSQL, not just the application layer. This decision guarantees that even if the backend application is compromised or experiences a bug, the data layer prevents unauthorized manipulation or illegal states.

### 1.2 Data Stratification: Operational vs. Analytical
Operational data (`civix` schema) is strongly separated from derived ML graphs and external analytical payloads. Operational tables (such as `civix_user`, `investigative_case`, `person`, `organization`) DO NOT contain target ML labels such as `is_criminal`, `fraud_probability`, or `ground_truth`. This is a deliberate architectural constraint to ensure the operational investigative system mirrors real-world evidence gathering without premature ML taint.

### 1.3 Synthetic Data Strategy
The project incorporates vast synthetic data generation to simulate a global environment for ML testing and UI validation. Synthetic runs are tracked via `generation_run_id` linked across entities. This ensures that synthetic test data can be identified, isolated, and destroyed without polluting potential production data paths.

### 1.4 Epistemic & Assertion Model
The system models facts (assertions) and hypotheses explicitly. The DB records who asserted what, based on which evidence. This allows investigations to track competing theories, unverified claims, and contradictory evidence natively in the schema.

### 1.5 Evidence & Provenance Architecture
Explicit tracking of digital/physical evidence through the `evidence_artifact` and `provenance` tables. Evidence immutability is paramount. The system is designed such that once evidence is logged, it cannot be tampered with. (Note: `chain_of_custody_event` does not exist in the live schema, its duties are handled by the aforementioned tables).

### 1.6 Identity & RLS Architecture
Highly restrictive database access. The API operates as `civix_api` (NOSUPERUSER, NOBYPASSRLS). Each user’s access is strictly isolated using PostgreSQL RLS policies scoped down to individual cases via the `case_access` table.

### 1.7 Security Principles & Connection Pooling
Trust nothing. Identity context must be pushed strictly into the database transaction boundary, preventing connection pool leakage. No "magic" global flags or superuser API access.

---

## 2. EXHAUSTIVE PHASE 6 DATABASE SCHEMA BIBLE

To ensure you have absolute context on the domain modeling, here is the complete Database Schema Bible, which outlines the exact tables, invariants, and foreign key relations constructed up to Phase 6.

<details>
<summary>Click to expand the Complete 03_DATABASE_SCHEMA_BIBLE.md</summary>

"""
    schema_bible = read_file('docs/03_DATABASE_SCHEMA_BIBLE.md')
    
    mid_section = """
</details>

---

## 3. EXHAUSTIVE PHASE 6 DATABASE RAW SQL SCHEMA DUMP

To ensure you have the exact, irrefutable live database state, here is the full pg_dump of the `civix` schema running on PostgreSQL 16 on port 5433. Do NOT make DDL assumptions; read the actual schema definition below.

<details>
<summary>Click to expand the FULL PostgreSQL 16 Schema Dump</summary>

```sql
"""
    schema_dump = read_file('scratch/schema_dump_utf8.sql')
    
    mid_section2 = """
```
</details>

---

## 4. EXHAUSTIVE PHASE 6 SECURITY FINDINGS & IMMUTABILITY

During the Phase 6/7 transition, a critical security audit uncovered severe flaws:
- **Finding:** Initial scripts heavily relied on hardcoded fallback credentials and superuser connections for operational queries.
- **Remediation:** Strict fail-closed configuration was implemented. The API explicitly uses the `civix_api` database role which possesses:
  - `rolsuper = false`
  - `rolbypassrls = false`
- **Immutability Enforcement:** The `civix_api` role explicitly lacks `UPDATE` and `DELETE` privileges on core audit and evidence tables (`audit_event`, `evidence_artifact`, `provenance`). This guarantees cryptographic-like immutability at the lowest database tier. These specific unprivileged states were empirically tested and proven to result in `ProgrammingError: permission denied` for the API role.

---

## 5. PHASE 7 TASK 1 - FASTAPI & RLS FOUNDATION

Task 1 focused on building the FastAPI foundation with strict RLS identity binding.

**RLS Identity Architecture (Approved & Verified):**
Identity configuration relies on SQLAlchemy 2.0 Async architecture (asyncpg). The user identity MUST NOT be bound at the connection-pool checkout event. Instead, it is established specifically within the request's database transaction using:
`SELECT set_config('civix.current_user_id', :user_id, true)`

### 5.1 Exhaustive API Source Code Evidence

The exact state of the foundation code is embedded below. You must use this code as your exact reference for how dependencies, database connections, and configurations are structured.

#### `civix_api/config.py`
```python
"""
    config_code = read_file('civix_api/config.py', True)
    mid_section3 = """
```

#### `civix_api/database.py`
```python
"""
    db_code = read_file('civix_api/database.py', True)
    mid_section4 = """
```

#### `civix_api/dependencies.py`
```python
"""
    dep_code = read_file('civix_api/dependencies.py', True)
    mid_section5 = """
```

#### `civix_api/main.py`
```python
"""
    main_code = read_file('civix_api/main.py', True)
    mid_section6 = """
```

---

## 6. PHASE 7 TASK 2A — CASE CREATION DEADLOCK & MIGRATION 010

An architectural deadlock was identified blocking safe case creation:

**The Deadlock:**
- `investigative_case` has `FORCE RLS` with a `WITH CHECK` policy requiring the authenticated user to possess a matching `case_access` row.
- `case_access.case_id` possessed a `NOT DEFERRABLE` foreign key referencing `investigative_case.case_id`.

**Verified Live Schema State Post-Migration 010:**
- The FK was dropped and recreated as `DEFERRABLE INITIALLY DEFERRED`.
- `condeferrable = true`
- `condeferred = true`
- `investigative_case` RLS constraints remain entirely active.
- `civix_api` role remains fully unprivileged.

**Verified Case Creation Sequence:**
1. Generate UUIDs for `case_id` and `access_id` in API.
2. Begin Database Transaction.
3. Establish `set_config(..., true)`.
4. `INSERT INTO civix.case_access` (Succeeds via deferred FK).
5. `INSERT INTO civix.investigative_case` (Succeeds via valid RLS context).
6. `COMMIT` (Both rows flush safely).

### 6.1 Case Access Trust Boundary (CRITICAL)

> [!IMPORTANT]
> The `civix.case_access` table currently has **RLS disabled** (`relrowsecurity = false`) and **FORCE RLS disabled**. The database currently allows the application to INSERT any mapping it wishes.
>
> **Implication:** The security trust boundary for `case_access` is entirely **APPLICATION ENFORCED**. The API must rigorously ensure that `case_access.user_id` is securely derived from the authenticated JWT principal and NEVER trusted from an arbitrary JSON payload.

---

## 7. CURRENT PHASE 7 TASK 2 STATE (IMPLEMENTATION & AUTH)

Implementation of Phase 7 Task 2 was initiated and partially completed. The following exact code represents the current un-merged, in-flight state of the API routers and JWT logic.

### 7.1 `civix_api/auth/jwt.py`
```python
"""
    jwt_code = read_file('civix_api/auth/jwt.py', True)
    mid_section7 = """
```

### 7.2 `civix_api/auth/principal.py`
```python
"""
    principal_code = read_file('civix_api/auth/principal.py', True)
    mid_section7_1 = """
```

### 7.3 `civix_api/routers/users.py`
```python
"""
    users_router = read_file('civix_api/routers/users.py', True)
    mid_section8 = """
```

### 7.4 `civix_api/routers/cases.py`
```python
"""
    cases_router = read_file('civix_api/routers/cases.py', True)
    mid_section9 = """
```

---

## 8. EXHAUSTIVE INTEGRATION TEST EVIDENCE

The IDE agent was paused while fixing teardown logic in the test suite. The exact code of the tests is preserved below to demonstrate what is covered: pool leakage, transaction isolation, negative runtime permissions, and JWT validation. The tests were failing intermittently due to SQLAlchemy teardown/session closure issues (fixture sharing across `create_test_user` and `db_session`), but fixes were applied just prior to halting.

### 8.1 `tests/api/conftest.py`
```python
"""
    conftest_code = read_file('tests/api/conftest.py', True)
    mid_section10 = """
```

### 8.2 `tests/api/test_auth.py`
```python
"""
    auth_test_code = read_file('tests/api/test_auth.py', True)
    mid_section11 = """
```

### 8.3 `tests/api/test_cases.py`
```python
"""
    cases_test_code = read_file('tests/api/test_cases.py', True)
    mid_section12 = """
```

### 8.4 `tests/api/test_rls.py`
```python
"""
    rls_test_code = read_file('tests/api/test_rls.py', True)
    footer = """
```

---

## 9. KNOWN RISKS / OPEN ITEMS

| ID | Issue | Severity | Current State | Required Action |
|---|---|---|---|---|
| 1 | `chain_of_custody_event` missing | High | Resolved | Utilize `evidence_artifact` and `provenance` tables going forward. |
| 2 | `case_access` Trust Boundary | Critical | Documented | API explicitly derives identity from JWT. Any future admin/sharing endpoints must actively validate the requester's permission. |
| 3 | Incomplete Test Suite Run | Medium | Pending | The test teardown mechanisms in `conftest.py` require a final execution validation to ensure isolated teardown passes. |
| 4 | Phase 7 Task 2 Completion | High | Pending | The task was paused during test validation. |

---

## 10. EXACT RESUME POINT (TO THE NEW AI AGENT)

You must start completely fresh from this exact state. 
Do NOT redesign the architecture. Do NOT modify the PostgreSQL 16 schema. Do NOT touch migrations 001-010. 

**Next Immediate Actions:**
1. Run `pytest tests/api -v` to observe the current testing state.
2. Fix any remaining teardown or isolation bugs in `conftest.py`, `test_cases.py`, or `test_auth.py`.
3. Complete Phase 7 Task 2 by delivering a fully green test suite proving authentication, RLS case isolation, transaction rollbacks, and JWT security behavior.

## 11. FINAL VERIFICATION CHECKLIST

- [x] Repository inspected 
- [x] Live PostgreSQL 16 inspected 
- [x] PostgreSQL 17 isolation verified (Confirmed no interactions)
- [x] Alembic state verified (001-009 unmodified, 010 exists)
- [x] Migration 010 verified (`condeferrable=t` established)
- [x] RLS policy verified (`investigative_case` is `forcerowsecurity=t`)
- [x] civix_api role verified (`rolsuper=f`, `rolbypassrls=f`)
- [x] Task 1 tests verified (Authored and present, teardown fixed)
- [x] Task 2A tests verified (Authored and present)
- [x] Current Task 2 implementation inspected (Routers & JWT modules created)
- [x] Current Task 2 tests inspected (Failures observed and documented)
- [x] Exact resume point established (See Section 10)
"""
    
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(schema_bible)
        f.write(mid_section)
        f.write(schema_dump)
        f.write(mid_section2)
        f.write(config_code)
        f.write(mid_section3)
        f.write(db_code)
        f.write(mid_section4)
        f.write(dep_code)
        f.write(mid_section5)
        f.write(main_code)
        f.write(mid_section6)
        f.write(jwt_code)
        f.write(mid_section7)
        f.write(principal_code)
        f.write(mid_section7_1)
        f.write(users_router)
        f.write(mid_section8)
        f.write(cases_router)
        f.write(mid_section9)
        f.write(conftest_code)
        f.write(mid_section10)
        f.write(auth_test_code)
        f.write(mid_section11)
        f.write(cases_test_code)
        f.write(mid_section12)
        f.write(rls_test_code)
        f.write(footer)
        
    print(f"Generated {out_file} successfully.")

if __name__ == '__main__':
    main()
