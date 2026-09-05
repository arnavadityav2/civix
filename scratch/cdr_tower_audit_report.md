# CDR & Tower Intelligence — Phase A Audit Report
# CIVIX 2.0 | Generated: 2026-09-05

---

## 0. Hero World Baseline

**Hero SHA BEFORE audit**: `e520f5a618dc553b4d0b7cfb2579b5e37a56eb3e0c220d75b7677a5d7816369e`
**Status**: ✅ MATCHES CANONICAL — No mutations performed during Phase A (read-only)

---

## 1. Database — Entity Counts

| Entity Type     | Count   | Table                      | Primary Identifier         |
|-----------------|---------|----------------------------|----------------------------|
| PHONE_NUMBER    | 15,026  | `civix.phone_number`        | `msisdn` (VARCHAR 15)      |
| SIM             | 15,000  | `civix.sim`                 | `iccid` (VARCHAR 22)       |
| DEVICE          | 7,525   | `civix.device`              | `imei` (VARCHAR 17)        |
| IMEI (distinct) | 7,525   | `civix.device.imei`         | All devices have IMEI      |
| IMSI            | **0**   | `civix.sim.imsi`            | ⚠️ ALL NULL — zero IMSI values |
| MSISDN          | 15,026  | `civix.phone_number.msisdn` | All phone numbers populated |

### Schema: civix.phone_number
```
entity_id       UUID     NOT NULL  (PK, FK → entity)
msisdn          VARCHAR  NOT NULL
country_code    CHAR(3)  NOT NULL  (DEFAULT 'IND')
operator        TEXT     NULL
number_type     TEXT     NULL
```

### Schema: civix.sim
```
entity_id         UUID     NOT NULL  (PK, FK → entity)
iccid             VARCHAR  NOT NULL  (UNIQUE)
imsi              VARCHAR  NULL      ⚠️ 0 records populated
issuing_operator  TEXT     NULL
```

### Schema: civix.device
```
entity_id     UUID     NOT NULL  (PK, FK → entity)
imei          VARCHAR  NULL      (7,525 populated = 100%)
mac_address   VARCHAR  NULL      (0 populated)
device_type   TEXT     NOT NULL
manufacturer  TEXT     NULL
model         TEXT     NULL
```

---

## 2. Events — Telecom Event Counts

| Event Type        | Count | Notes                              |
|-------------------|-------|------------------------------------|
| CALL              | 328   | Confirmed. Timestamp = `occurred_at` (TSTZRANGE) |
| DEVICE_PING       | 249   | Confirmed                          |
| MESSAGE           | **0** | Zero MESSAGE events exist          |
| SURVEILLANCE_OBS  | 264   | Non-telecom                        |
| TRANSACTION       | 255   | Non-telecom                        |
| **TOTAL telecom** | **577** |                                  |

### Schema: civix.event
```
event_id          UUID       NOT NULL  (PK)
event_type        ENUM       NOT NULL
occurred_at       TSTZRANGE  NOT NULL  ← range type, not scalar
description       TEXT       NULL      ← Contains human-readable call summaries
source_record_id  UUID       NULL      ← FK → source_record
tx_start          TIMESTAMPTZ NOT NULL
generation_run_id UUID       NULL
```

**Critical finding**: `occurred_at` is a **TSTZRANGE** (not a scalar timestamp). Duration of a CALL = upper(occurred_at) - lower(occurred_at).

---

## 3. CALL Event — Relationship Schema Map

**Established actual structure via query:**

```
CALL event
  ├── event_participant (role=CALLER, entity_type=PHONE_NUMBER)  → A-party MSISDN
  ├── event_participant (role=CALLEE, entity_type=PHONE_NUMBER)  → B-party MSISDN
  ├── event_participant (role=PARTICIPANT, entity_type=PERSON)   → 208 records (PERSON participants)
  ├── event_participant (role=PARTICIPANT, entity_type=LOCATION) → 46 records (location participants)
  ├── event_location → location (location_type varies)           → case linkage
  └── source_record (type=EVENT_RECORD)                          → 74 of 328 have source records
```

**Key findings:**
- CALLER/CALLEE roles exist and correctly link to PHONE_NUMBER entities ✅
- IMEI is NOT stored on CALL events — must traverse PHONE_NUMBER → (no direct link to DEVICE)
- IMSI is NOT stored anywhere (sim.imsi = 0 rows)
- 254 CALL events have NO source_record (no provenance to raw CDR)
- 254 CALL events show as "PARTICIPANT" role → entity_type=PERSON (these are case-linked person associations, not telecom participants)
- Duration extractable from TSTZRANGE: `upper(occurred_at) - lower(occurred_at)` = ~30-55 second ranges observed

---

## 4. DEVICE_PING Event — Relationship Schema Map

```
DEVICE_PING event
  ├── event_participant (role=PARTICIPANT, entity_type=PERSON)    → 182 records
  ├── event_participant (role=PARTICIPANT, entity_type=LOCATION)  → 58 records
  ├── event_participant (role=SUBJECT,     entity_type=PHONE_NUMBER) → 6 records
  ├── event_participant (role=LOCATION,    entity_type=LOCATION)  → 6 records
  └── event_location → location (various types)                   → all 249 linked to cases
```

**Critical blockers found:**
- ❌ Zero DEVICE_PING events have a DEVICE entity participant — no IMEI linkable
- ❌ Zero DEVICE_PING events have a CELL_TOWER role participant
- Only 6 DEVICE_PING events have a PHONE_NUMBER participant (role=SUBJECT)
- Tower linkage via `event_location → location` where `location_type=CELL_SECTOR_POLYGON` works for **37 of 249** pings

---

## 5. Cell Tower / Cell Sector Audit

### Location Type Distribution
| Location Type         | Count |
|-----------------------|-------|
| CRIME_SCENE           | 415   |
| EXACT_POINT           | 282   |
| ESTIMATED_POINT       | 157   |
| GEOFENCE              | 129   |
| CELL_SECTOR_POLYGON   | **118** |
| ROUTE_LINESTRING      | 1     |

### Critical Finding: "118 CELL_SECTOR_POLYGON" vs "10 named towers"

The 118 CELL_SECTOR_POLYGON records are **NOT** 118 distinct real-world towers. Sample reveals:
- Many are named `"Investigative Location — [Area]"` (generic investigative locations tagged as CELL_SECTOR_POLYGON)
- Only a small subset have actual "Cell Tower" naming conventions (e.g., `"Kashmere Gate Cell Tower"`, `"Golf Course Road Cell Tower"`)
- Named CELL/TOWER locations total only 10: `Cell Tower DW-01 Dwarka`, `Cell Tower NJ-01 Najafgarh`, `Cell Tower NH-48 Highway`, `Cell Tower Rohini`, `Cell Tower IGI Airport Zone`, `Cell Tower Chandni Chowk`, plus 2 CELL_SECTOR_POLYGONs named properly
- **azimuth_degrees** = NULL for all sampled records → no sector directional data
- **beamwidth_degrees** = NULL → no angular spread data

### CELL_SECTOR_POLYGON in event_location (all event types)
```
SURVEILLANCE_OBSERVATION: 40
TRANSACTION:              40
DEVICE_PING:              37  ← Only 37 of 249 pings have cell sector linkage
CALL:                     34  ← Only 34 of 328 calls have cell sector linkage
FIR_FILING:               29
SEIZURE:                  27
...
```

**Conclusion**: The "CELL_SECTOR_POLYGON" type is being used as a general-purpose coverage area label for investigative locations, not exclusively for real cell tower sectors.

---

## 6. Tower Hit / Ping Metrics

| Metric                                    | Count |
|-------------------------------------------|-------|
| Total DEVICE_PING events                  | 249   |
| PINGS_WITH_CELL_TOWER participant         | 0     |
| PINGS_WITH_LOCATION participant           | 6     |
| PINGS_IN_EVENT_LOCATION                   | 249   |
| PINGS_WITH_CASE (via event_location)      | 249   |
| PINGS_WITH_CELL_SECTOR (via event_location)| 37   |
| PINGS_WITH_DEVICE entity                  | 0     |
| PINGS_WITH_PHONE entity                   | 6     |

**Spatial mapping capability**:
- 37 of 249 pings can be mapped to a CELL_SECTOR_POLYGON location
- Tower dump query IS feasible for these 37 via `event_location → location(CELL_SECTOR_POLYGON)`
- Geometry exists on location rows (PostGIS) but centroid derivation needed for map display

---

## 7. CDR Evidence Audit

- **CDR_ROW source_record rows**: 0 (none found)
- **Evidence document source_records**: 408 of type `EVIDENCE_DOCUMENT`
- **EVENT_RECORD source_records**: 150 of type `EVENT_RECORD`
- **FIR_DOCUMENT**: 12

EVD-001-004 etc. exist as `external_reference` values on `EVIDENCE_DOCUMENT` type source_records.

**Conclusion**: CDR evidence is Type B — "Merely attached evidence documents." There are NO structured CDR_ROW records in `source_record`. The CALL events with descriptions like _"CDR analysis confirms contact..."_ were generated as narrative text, not as parsed CDR data rows.

---

## 8. SIM/IMEI Reuse Analysis

| Metric                      | Count | Notes                                     |
|-----------------------------|-------|-------------------------------------------|
| `sim_in_device` rows        | **0** | ⚠️ Table is empty — no SIM↔DEVICE relationships |
| `sim_number_assignment` rows| **0** | ⚠️ Table is empty — no SIM↔PHONE assignments |
| Assertions: USED_SIM        | 2     | Graph assertions exist for 2 pairs        |
| Assertions: HAD_NUMBER      | 1     | One phone→number assertion                |
| Assertions: USED_DEVICE     | 1     | One device assertion                      |

**Conclusion**: 
- `sim_in_device` and `sim_number_assignment` tables are completely empty
- SIM swap detection is **IMPOSSIBLE** from structured data
- The 15,000 SIMs and 7,525 devices exist as standalone entities with NO relationship tables populated
- Only 4 telecom assertions exist in `civix.assertion` — completely insufficient for analysis

---

## 9. Cross-Case Telecom Intelligence

- **Shared phones** (PHONE_NUMBER in >1 case via case_entity_role): **0**
- **Shared devices** (DEVICE in >1 case via case_entity_role): **0**
- **Shared SIMs** (SIM in >1 case via case_entity_role): **0**

**Finding**: No telecom entities appear in more than one case. Cross-case telecom intelligence cannot be derived from this dataset as it currently stands.

---

## 10. Case ↔ Telecom Event Linkage

Each case has at most 1 CALL and 1 DEVICE_PING linked via `event_location`:
```
SYN-2025-001: CALL=1, DEVICE_PING=1
SYN-2025-002: CALL=1, DEVICE_PING=1
...
```

**Finding**: The event-to-case linkage is 1:1 per event type per case. The synthetic world generator created exactly 1 CALL and 1 DEVICE_PING per case. Not a CDR dataset — it is an investigation event timeline.

Golden cases (CIV-*, GLD-*): **0 telecom events**

---

## 11. Neo4j Status

**Neo4j**: OFFLINE (port 7688, connection refused)

**Decision**: The entire telecom API will be built 100% on PostgreSQL. Neo4j is NOT a dependency.

---

## 12. Hardcode Audit Results

- Existing `frontend/src` files: **0 hardcoded telecom intelligence strings** found
- No `const calls = [...]` or `const towers = [...]` found
- No `totalPings`, `IMEI-A`, `TOWER-DW-01` found
- The existing "CDR & Tower Dump" sidebar link points to `/spatial` — no fake data embedded

---

## 13. Analytical Capability Assessment

| Capability          | Status   | Reason                                                                 |
|---------------------|----------|------------------------------------------------------------------------|
| CDR Inspector       | PARTIAL  | CALL/PING events exist; CALLER/CALLEE roles populated; no IMEI/SIM/device linkage |
| Tower Dump          | PARTIAL  | 37 pings linkable to cell sectors; no DEVICE in pings; phone linkage = 6 only |
| Co-location         | PARTIAL  | 6 events have phone + tower in same event; extremely sparse            |
| SIM/IMEI Matrix     | BLOCKED  | sim_in_device=0, sim_number_assignment=0, IMSI=0                      |
| Tower Mapping       | PARTIAL  | 118 CELL_SECTOR_POLYGON locations with geometry; linkable via event_location |
| Cross-case Telecom  | BLOCKED  | No telecom entities shared across cases                                |

---

## 14. Phase B Blocker Summary

### P0 — Critical Blockers

| Blocker ID | Description                                                                      |
|------------|----------------------------------------------------------------------------------|
| BLK-T01    | `sim_in_device` table is empty — no SIM↔DEVICE relationships exist              |
| BLK-T02    | `sim_number_assignment` table is empty — SIM↔MSISDN assignments unknown         |
| BLK-T03    | Zero IMSI values in `civix.sim` — IMSI-based lookup impossible                  |
| BLK-T04    | DEVICE_PING events have no DEVICE entity participant — IMEI cannot be resolved   |
| BLK-T05    | 254 of 328 CALL events have no source_record — no CDR provenance                 |
| BLK-T06    | 0 golden/hero case telecom events — real investigation data has no CDR           |

### P1 — Structural Gaps

| Blocker ID | Description                                                                      |
|------------|----------------------------------------------------------------------------------|
| BLK-T07    | CELL_SECTOR_POLYGON misuse — 118 records are generic investigative locations     |
| BLK-T08    | No DEVICE or SIM participants on DEVICE_PING events                              |
| BLK-T09    | No cross-case telecom entity sharing                                             |

### Cannot-Remediate (Data Integrity Constraint)

| Item                           | Reason                                                        |
|--------------------------------|---------------------------------------------------------------|
| IMSI population                | IMSI was never seeded; cannot be invented                    |
| SIM swap detection             | sim_in_device is empty; no temporal SIM relationship data    |
| CDR_ROW source records         | Raw CDR was never ingested as structured rows                 |
| Golden case telecom events     | Hero cases have no CALL/PING events; cannot add (Hero-safe)  |
| Cross-case telecom             | Synthetic world generates isolated cases                      |

---

## 15. What CAN Be Built (READY)

Despite the blockers, the following IS supportable from existing data:

1. **CDR Event Log** — CALL events with CALLER/CALLEE MSISDN, timestamp, duration (from TSTZRANGE), description, case linkage → **READY**
2. **Device Ping Log** — DEVICE_PING events with timestamp, case, location → **READY**  
3. **Tower Map** — Display CELL_SECTOR_POLYGON locations with geometry and event hit counts → **READY** (labeled correctly as investigative locations)
4. **Tower Dump (partial)** — For the 37 pings linked to cell sectors, return all observable phones → **PARTIAL**
5. **Telecom Summary** — Real counts: calls, pings, unique phones, unique towers per case → **READY**
6. **Telecom Entities** — Phone numbers, devices, SIMs linked to a case via case_entity_role → **READY**

---

## 16. CALL Event Description Samples (confirm these are narrative, not structured CDR)

```
"CDR analysis confirms contact between accused persons at a time consistent with operational planning."
"Intercept analysis confirms suspect placed a 4-minute call to an unregistered number immediately following the incident."
"Target placed multiple calls to shell company directors on the day of the fraudulent transfer."
```

These are generated narrative descriptions, NOT structured CDR field data. The TSTZRANGE duration IS real (30-55 second intervals = actual modeled call lengths).

---

## Summary Table (Final)

```
Database:
  PHONE_NUMBER:    15,026
  SIM:             15,000
  DEVICE:          7,525
  IMEI:            7,525
  IMSI:            0

Events:
  CALL:            328
  MESSAGE:         0
  DEVICE_PING:     249
  TOTAL:           577

Towers:
  CELL SECTORS:    118 (location table, CELL_SECTOR_POLYGON type)
  ACTUAL TOWERS:   ~8 (distinctly named cell towers)
  MAPPED PINGS:    37 (linked to CELL_SECTOR_POLYGON via event_location)
  UNMAPPED PINGS:  212

Evidence:
  CDR artifacts:         0 (CDR_ROW type source_records)
  Evidence documents:    408
  Structured CDR data:   0

Relationships:
  sim_in_device:         0 rows
  sim_number_assignment: 0 rows
  PHONE → CASE:          via case_entity_role (data exists)
  DEVICE → CASE:         via case_entity_role (data exists)
  TOWER → CASE:          via event_location → location (37 pings)

Cross-case:
  shared phones:  0
  shared devices: 0
  shared SIMs:    0
  shared IMEIs:   0
  shared towers:  0 (no cross-case linking found)

Analytical capability:
  CDR Inspector:       PARTIAL
  Tower Dump:          PARTIAL
  Co-location:         BLOCKED (only 6 events with phone+tower)
  SIM/IMEI Matrix:     BLOCKED (no sim_in_device, no sim_number_assignment)
  Tower Mapping:       PARTIAL
  Cross-case Telecom:  BLOCKED

Neo4j:               OFFLINE

Hardcoding:
  hardcoded telecom intelligence: NONE FOUND
  mock datasets:                  NONE FOUND
  fake fallback values:           NONE FOUND
```