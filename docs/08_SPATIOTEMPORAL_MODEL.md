# 08 — Spatiotemporal Model Bible
**Version**: 1.0 | **Date**: 2026-08-29

---

## 1. Spatial Model

All spatial data is stored using PostGIS GEOMETRY types in SRID 4326 (WGS84).

### 1.1 Location Types

| Type | Geometry | Use Case |
|---|---|---|
| `EXACT_POINT` | POINT | Known GPS coordinate (e.g., building address) |
| `ESTIMATED_POINT` | POINT + `uncertainty_radius_meters` | Approximate location |
| `CELL_SECTOR_POLYGON` | POLYGON | Cell tower sector coverage area |
| `CCTV_COVERAGE_POLYGON` | POLYGON | CCTV camera field of view |
| `PROPERTY_BOUNDARY` | POLYGON | Cadastral land boundary |
| `CRIME_SCENE` | POLYGON | Defined crime scene boundary |
| `GEOFENCE` | POLYGON | Investigative perimeter |
| `ADMIN_BOUNDARY` | POLYGON | District/taluka boundary |
| `ROUTE_LINESTRING` | LINESTRING | Vehicle/person travel path |

> [!IMPORTANT]
> **BLK-05 RESOLUTION (ADR-016)**
> The generator output references locations (`LOC-*`) and cell towers (`CELL-*`) but does not output coordinates.
> A separate file `docs/location_master.json` contains the canonical PostGIS coordinate definitions for these entities within Ajmer district. It is a derived artifact, not part of the frozen generator config.

### 1.2 Cell Tower Semantics (CRITICAL)

CDR data contains `location_cell` fields like `CELL-01`, `CELL-17`, `CELL-47`.

**These are NOT the user's location.**

Correct mapping:
```
CELL-01 → location(entity_id=L-01, location_type=CELL_SECTOR_POLYGON,
                   geometry=ST_GeomFromText('POLYGON((...))'), azimuth_degrees=120,
                   beamwidth_degrees=120, uncertainty_radius_meters=5000)
```

**Inferences from cell data**:
- "Device D was pinging tower T" → `event_participant(PING_SOURCE, device D)` + `event_participant(CELL_TOWER, location L)`
- "Person P was within the coverage area of CELL-01" → `extraction` (AI inference) not `assertion(SEEN_AT)` from human observation
- Two people pinging the same cell tower does NOT imply co-location — cell sectors cover several km²

### 1.3 Spatial Queries

Key PostGIS operations:
```sql
-- Are two cell sectors overlapping? (potential co-location zone)
SELECT ST_Intersects(a.geometry, b.geometry)
FROM civix.location a, civix.location b
WHERE a.entity_id = $cell_a AND b.entity_id = $cell_b;

-- How large is a cell sector?
SELECT ST_Area(geometry::geography) AS area_sq_meters
FROM civix.location WHERE entity_id = $cell_id;

-- Is a property within a geofence?
SELECT ST_Within(p.boundary_geometry, g.geometry)
FROM civix.property p, civix.location g
WHERE g.location_type = 'GEOFENCE';
```

---

## 2. Temporal Model (Bitemporal)

CIVIX uses a bitemporal model with TWO time dimensions:

| Dimension | Column Pattern | Meaning |
|---|---|---|
| **Valid Time** | `valid_from / valid_to` or `valid_time TSTZRANGE` | When the fact was true in the REAL WORLD |
| **Transaction Time** | `tx_start / tx_end` | When CIVIX recorded or superseded this fact |

### 2.1 Valid Time
- When was this true in reality?
- Example: "SIM-001 had number 9876543210 from June 1, 2026 to August 15, 2026"
- Stored as `valid_time TSTZRANGE` in `sim_number_assignment`

### 2.2 Transaction Time
- When did CIVIX know this?
- `tx_start = now()` on INSERT, `tx_end = now()` when superseded
- Immutable rows never get `tx_end` set

### 2.3 Event Time
- `event.occurred_at TSTZRANGE` represents when the event happened in the real world
- Using `TSTZRANGE` (not `TIMESTAMP`) correctly captures uncertainty:
  - Known call: `[2026-08-13 14:33:22, 2026-08-13 14:35:47]` (exact bounds)
  - Approximate meeting: `[2026-07-15 00:00:00, 2026-07-16 00:00:00]` (date-level precision)
  - Unknown date: `(-inf, +inf)` is possible but should trigger a `data_quality_issue`

### 2.4 Temporal Exclusion Constraints

Physical laws enforced via GIST exclusion:
```sql
-- A SIM cannot be in two devices simultaneously
EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&)
ON civix.sim_in_device;

-- A phone number cannot be assigned to two SIMs simultaneously
EXCLUDE USING GIST (phone_number_id WITH =, valid_time WITH &&)
ON civix.sim_number_assignment;
```

These are PHYSICAL constraints (hardware/telecom engineering realities).

**Do NOT apply exclusion constraints to**:
- `assertion(USED_DEVICE)` — a person's claimed device use is epistemic, not physical
- `case_entity_role` — a person may have multiple roles in one case
- `account_holder` — joint accounts have simultaneous holders

### 2.5 AS-OF Queries (Historical Reconstruction)

```sql
-- What did CIVIX know about this assertion as of June 30, 2026?
SELECT * FROM civix.assertion
WHERE assertion_id = $id
  AND tx_start <= '2026-06-30'
  AND (tx_end IS NULL OR tx_end > '2026-06-30');

-- Who held this account as of July 15, 2026?
SELECT * FROM civix.account_holder
WHERE account_id = $id
  AND valid_time @> '2026-07-15'::TIMESTAMPTZ;
```

### 2.6 Preventing Future Data Leakage

ML models must not see data that was not yet known at the training snapshot time:

```sql
-- Feature extraction AS OF August 1, 2026 (no data added after this date should be visible)
SELECT * FROM civix.assertion
WHERE tx_start <= '2026-08-01'
  AND generation_run_id IS NOT NULL  -- only synthetic data for training
  AND (tx_end IS NULL OR tx_end > '2026-08-01');
```

---

## 3. Uncertain Dates

Investigation data frequently has uncertain or approximate dates. Rules:

| Situation | Approach |
|---|---|
| Date known, time unknown | `[2026-07-15 00:00:00, 2026-07-16 00:00:00)` range |
| Only month known | `[2026-07-01 00:00:00, 2026-08-01 00:00:00)` range |
| Approximate ("mid-August") | Wide range + `data_quality_issue(IMPOSSIBLE_TIMESTAMP)` if contradicted |
| Unknown date | NULL with mandatory `data_quality_issue(MISSING_REQUIRED_FIELD)` |

Never store `9999-12-31` as "unknown" — use NULL + data quality issue.
