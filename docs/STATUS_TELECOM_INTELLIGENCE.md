# CIVIX 2.0 — Telecom / CDR & Tower Intelligence Status Checkpoint

**Subsystem**: Telecom / CDR & Tower Intelligence  
**Current Status**: PAUSED / FROZEN FOR LATER RESUMPTION  
**Latest Completed Phase**: Phase 7.6 — API Integration & Remediation Validation  
**Phase Verdict**: PASS  
**Tier 3 Status**: APPROVED BUT NOT STARTED (Intentionally Deferred)  
**Last Verified Date**: September 5, 2026  

---

> [!NOTE]
> **Subsystem Freeze Notice**: Development on the Telecom / CDR & Tower Intelligence workstation is deliberately **PAUSED** to allow development to focus on other CIVIX 2.0 product subsystems.  
> 
> "Paused" does **NOT** mean "failed" or "unfinished." The Telecom subsystem has reached a fully validated, production-grade, isolated checkpoint. All Phase 7.6 remediations are verified 100% PASS. Further dataset scaling (Tier 3) is intentionally deferred.

---

## 1. Subsystem Architecture & Routing Isolation

The Telecom Intelligence Subsystem uses strict database and route-level isolation between the **Primary CIVIX World** and the **Synthetic Telecom Benchmark**.

### Request Routing Architecture

```
                       FastAPI Backend Route Entry
                                   |
                  +----------------+----------------+
                  |                                 |
        Case Prefix Check                  Case Prefix Check
         (CIV-* / SYN-*)                       (BENCH-*)
                  |                                 |
                  v                                 v
        Primary CIVIX Schema           civix_telecom_benchmark Schema
       (civix.investigative_case)     (civix_telecom_benchmark.benchmark_case)
                  |                                 |
     +------------+------------+                    +---------------+
     |            |            |                    |               |
  civix.       civix.       civix.              benchmark_       benchmark_
  event        entity     phone_number           event             phone
  (etc)        (etc)        (etc)                (etc)             (etc)
```

### Architectural Protection Rules

1. **NO Dynamic `search_path` Manipulation**: The API MUST NEVER execute `SET search_path` dynamically based on user/request input. All SQL statements must be explicitly schema-qualified (`civix.*` vs `civix_telecom_benchmark.*`).
2. **Explicit Namespace Partitioning**:
   * `CIV-*` / `SYN-*` case requests route **exclusively** to the `civix.*` primary schema.
   * `BENCH-*` case requests route **exclusively** to `civix_telecom_benchmark.*`.
3. **No Fallback Contamination**: If a `BENCH-*` case identifier is not found in `civix_telecom_benchmark.benchmark_case`, the API returns `404 Not Found`. It MUST NEVER fall back to searching the primary `civix.investigative_case` registry.
4. **Primary Case Guard**: The `get_benchmark_case_phones` endpoint returns `400 Bad Request` if called with a non-`BENCH-` prefix (e.g. `PRIMARY-CASE-001`), protecting primary case routing.

---

## 2. Completed Capabilities Ledger

### Backend API (`civix_api/routers/telecom.py`)

- [x] **Case-Scoped Telecom Events** (`GET /api/v1/cases/{case_id}/telecom/events`): Supports filtering by `event_type` (`CALL`, `DEVICE_PING`, `MESSAGE`) and `msisdn`. Dual-routed for `BENCH-` and primary cases.
- [x] **Telecom Entities** (`GET /api/v1/cases/{case_id}/telecom/entities`): Lists phone numbers, SIMs, and devices with usage metrics and time bounds.
- [x] **Case Telecom Towers** (`GET /api/v1/cases/{case_id}/telecom/towers`): Returns linked cell sector polygons with hit counts and observation windows.
- [x] **Tower Dump Analysis** (`GET /api/v1/telecom/tower-dump`): Analyzes all observable events at a cell sector during a specified time window.
- [x] **Co-Location Analysis** (`GET /api/v1/telecom/co-location`): Identifies spatial-temporal overlaps between two MSISDNs at common cell sector polygons within a configurable time window (`overlap_window_seconds`).
- [x] **Device / SIM Matrix** (`GET /api/v1/telecom/device-sim-matrix`): Matrix listing device IMEI to SIM ICCID/IMSI pairings.
- [x] **Benchmark Case Discovery** (`GET /api/v1/telecom/benchmark/cases`): Returns available synthetic benchmark cases.
- [x] **Dynamic Case Phone Discovery** (`GET /api/v1/telecom/benchmark/case-phones`): Dynamically fetches active MSISDNs associated with a benchmark case (added in Phase 7.6 remediation).

### Frontend Workstation (`frontend/src/pages/TelecomIntelligencePage.tsx` & `frontend/src/api/telecom.ts`)

- [x] **Benchmark Case Selection & Switching**: Full UI support for switching between `BENCH-TELECOM-001`, `BENCH-TELECOM-002`, and primary cases.
- [x] **Dynamic MSISDN Selector**: Phone selection dropdown dynamically populated via `fetchBenchmarkCasePhones` (remediated H-1 gap).
- [x] **Co-Location Controls & Pagination**: Includes time window slider, distance parameters, and `Prev`/`Next` page controls consuming backend pagination metadata (`total`, `page`, `page_size`, `total_pages`).
- [x] **Provenance Badge Alignment**: Mappings clearly differentiate `PRIMARY CASE` (blue) vs `GOLDEN BENCHMARK` (purple).
- [x] **Stale State Cleanup**: `useEffect` state reset prevents bleeding of tower dumps, co-location results, and target phone selections across case switches.

---

## 3. Validated Tier-2 Benchmark State

The synthetic telecom benchmark exists in the `civix_telecom_benchmark` schema inside `civix_demo`.

### Validated Table Counts (`civix_telecom_benchmark`)

| Table Name | Validated Record Count | Notes / Description |
|---|---|---|
| `benchmark_case` | **2** | `BENCH-TELECOM-001` (Suspect Movement) & `BENCH-TELECOM-002` (Co-location / SIM Swap) |
| `benchmark_event` | **3,021** | 3,000 Tier-2 events + 21 Phase 7.6 remediated events (15 calls, 6 pings for shared entities) |
| `benchmark_tower` | **20** | Delhi NCR cell sector coverage polygons |
| `benchmark_phone` | **1,207** | Synthetic MSISDNs (10-digit Indian numbers) |
| `benchmark_device` | **38** | Synthetic IMEIs |
| `benchmark_sim` | **32** | Synthetic ICCIDs |
| `benchmark_sim_device_link` | **5** | SIM-swap link records |
| `benchmark_cross_case_link` | **5** | Cross-case entity links |
| `generation_run` | **2** | Record of active run & historical orphaned run |

### Active Benchmark Generation Run
* **Current Run ID**: `0349c49f-2522-4f33-9812-0e1b700bab9c` (Tier 2, Target Run `20260905`)
* **Historical Run ID**: `04af478d-69cf-4f00-9f47-b92d93805d52` (Tier 1 run, preserved for audit; **DO NOT DELETE**)

---

## 4. Primary CIVIX World Protection Guarantees

The primary CIVIX dataset (`civix.*` schema in `civix_demo`) is strictly protected from benchmark activity.

### Validated Primary Table Counts (`civix`)

| Primary Table | Validated Count | Protection Status |
|---|---|---|
| `civix.investigative_case` | **267** | Intact — 0 benchmark rows added |
| `civix.event` | **2,201** | Intact — 0 benchmark rows added |
| `civix.event_participant` | **2,251** | Intact — 0 benchmark rows added |
| `civix.entity` | **60,796** | Intact — 0 benchmark rows added |
| `civix.phone_number` | **15,026** | Intact — 0 benchmark rows added |
| `civix.sim` | **15,000** | Intact — 0 benchmark rows added |
| `civix.device` | **7,525** | Intact — 0 benchmark rows added |

### Protection Checklist
- [x] **Hero / Golden Cases**: **13/13** Hero cases verified 100% intact with unchanged cryptographic integrity hashes.
- [x] **No Case Registry Injection**: Benchmark cases are stored solely in `civix_telecom_benchmark.benchmark_case`.
- [x] **Zero Foreign Keys**: 0 cross-schema FK constraints between `civix_telecom_benchmark` and `civix`.
- [x] **Zero CDC / Outbox Triggers**: Benchmark inserts do not fire outbox triggers or generate CDC stream events.
- [x] **Zero Neo4j Contamination**: Benchmark entities/events are not projected into `:7688` Neo4j graph instances (`civix_demo_graph`).
- [x] **Zero ML Contamination**: Benchmark events do not contaminate behavioral XGBoost training data or model features.

---

## 5. Analytical Findings & Remediation Summary

During Phase 7.5 review and Phase 7.6 remediation, key analytical findings were established:

1. **Co-Location Detection Mechanics**:
   * Initial zero-result observations during Phase 7.5 manual testing were caused by using US placeholder MSISDNs (`+1-555-0100`) in test queries against synthetic Indian 10-digit MSISDNs (`9892755291`), rather than an API defect.
   * `BENCH-TELECOM-002` contains high spatial-temporal overlap (10,233 co-location matches discovered across the case timeline).
   * Co-location endpoints return Cartesian matches for high-density phone pairs; pagination (`page`, `page_size`) was implemented in Phase 7.6 to constrain response payloads.
2. **Cross-Case Shared Entity Activity**:
   * Phase 7.6 injected 21 synthetic events into `BENCH-TELECOM-002` for shared phones (`+1-555-0100` to `0102`) and devices (`DEV-1001` / `1002`). Cross-case link analysis now detects real investigative overlaps between `BENCH-TELECOM-001` and `BENCH-TELECOM-002`.
3. **Query Performance Profile**:
   * Tower dumps and co-location queries on benchmark datasets involve non-trivial spatial-temporal join logic (`ST_Centroid` / `TSTZRANGE` bounds). At Tier-2 volume (~3,000 events), response times remain < 150ms. Higher density (Tier 3) will require indexed spatial joins.

---

## 6. Deferred Work

## DEFERRED — DO NOT WORK ON NOW

The following work items are explicitly **DEFERRED** until Telecom work is formally resumed:

- [ ] **Tier-3 Benchmark Dataset Scale-Up**: Expanding synthetic benchmark density to ~10,000–50,000+ events across multiple cases. (*Tier 3 is APPROVED in principle, but NOT AUTHORIZED for execution during this freeze.*)
- [ ] **Large-Volume Telecom Stress Testing**: Benchmarking query latency at 50k+ event scale.
- [ ] **Advanced Spatial Sector Analysis**: Incorporating directional beamwidth and azimuth calculations into spatial joins.
- [ ] **Cross-Case Network Visualization**: Rendering interactive multi-case graph views for telecom entities.
- [ ] **Additional Telecom Scenario Generation**: Creating Tier-3 cell tower spoofing or IMEI hopping benchmark cases.

---

# DO NOT TOUCH WHILE TELECOM IS PAUSED

While the Telecom subsystem is paused, future AI agents and developers **MUST NOT**:

1. **Do NOT** regenerate or scale benchmark data in `civix_telecom_benchmark`.
2. **Do NOT** execute Tier 3 data generation scripts.
3. **Do NOT** modify primary CIVIX telecom tables (`civix.event`, `civix.phone_number`, `civix.device`, `civix.sim`).
4. **Do NOT** alter Hero/Golden case data or integrity validation rules.
5. **Do NOT** modify benchmark routing logic in `civix_api/routers/telecom.py`.
6. **Do NOT** introduce dynamic `search_path` changes in database connections.
7. **Do NOT** merge benchmark records into global `/api/v1/cases` endpoints.
8. **Do NOT** introduce hardcoded MSISDNs in `TelecomIntelligencePage.tsx`.
9. **Do NOT** remove provenance badges or synthetic flags.
10. **Do NOT** link `civix_telecom_benchmark` to CDC outbox triggers, Neo4j, or ML training pipelines.

---

# WHEN WE RESUME TELECOM

When authorization is given to resume work on the Telecom / CDR & Tower Intelligence subsystem, the next planned step is:

**PHASE 7.7 / TIER 3 REVIEW → CONTROLLED TIER-3 SCALING AND VALIDATION**

### Resumption Execution Checklist

Before writing any code or executing any generator scripts upon resumption:

1. **Read This Document**: Review `docs/STATUS_TELECOM_INTELLIGENCE.md` to re-establish context.
2. **Inspect Current Code**: Check `civix_api/routers/telecom.py` and `frontend/src/pages/TelecomIntelligencePage.tsx`.
3. **Verify Primary CIVIX Counts**: Run `SELECT COUNT(*)` on `civix.investigative_case` (267), `civix.event` (2,201), `civix.entity` (60,796) to confirm 0 primary contamination occurred while paused.
4. **Verify Hero Case Integrity**: Validate that all 13 Hero cases remain intact.
5. **Verify Benchmark Schema State**: Confirm `civix_telecom_benchmark.benchmark_event` count (3,021) and active run ID (`0349c49f-2522-4f33-9812-0e1b700bab9c`).
6. **Execute Read-Only Baseline API Check**: Run `scratch/phase76_validate.py` to confirm all remediated endpoints respond with 200 OK.
7. **Define Exact Tier-3 Target Volume**: Confirm exact target event/tower/phone counts with the human before running generator scripts.
8. **Preserve Schema Isolation**: Ensure Tier-3 scripts target `civix_telecom_benchmark` schema ONLY.
9. **Validate Performance**: Run controlled scale-up (~10,000 events per case first) and verify co-location query response times before any further scale increases.
