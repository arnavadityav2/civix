# CIVIX 2.0 — MASTER INDEX & CANONICAL VERSIONS
## Version 1.0 | Governance Document | Resolves All Known Conflicts

> [!IMPORTANT]
> This document is the FIRST file to read before executing any materialization, image generation, or database seeding script. It resolves all known ambiguities, retires duplicate files, and locks the canonical ID conventions for the entire Presentation Universe.

---

## 1. CANONICAL FILE REGISTRY

All files residing in `docs/presentation_universe/` and their canonical status:

| Filename | Purpose | Canonical Status | Authority |
|:---|:---|:---|:---|
| `00_INDEX_AND_CANONICAL_VERSIONS.md` | **This file.** Master governance index. | **CANONICAL** | Source of truth for all conflicts |
| `01_Universe_Bible_Part1.md` | Universe overview, design philosophy, 12 Hero Cases, Corridors A–H | **CANONICAL** | Primary universe specification |
| `CIVIX_2.0_UNIVERSE_BIBLE_V4.md` | Identical copy of Part1 | **DEPRECATED** | Do not edit or reference for new work |
| `02_Universe_Bible_Part2_CaseMatrix.md` | Full FIR-level spec for all 55 cases (CIVIX-001 through CIVIX-055) | **CANONICAL** | Primary case specification |
| `CIVIX_2.0_UNIVERSE_BIBLE_PART_3.md` | Entity rosters: Persons, Orgs, Vehicles, Telecom, Identity Candidates | **CANONICAL** | Primary entity specification |
| `CIVIX_2.0_PERSONS_PHOTO_MANIFEST.md` | Photo sourcing/generation spec for ~260 persons | **CANONICAL** | Image generation authority |
| `CIVIX_2.0_CASES_EVIDENCE_MANIFEST.md` | Evidence specs for CIVIX-001 to CIVIX-003 only (47 cases are stubs) | **CANONICAL (PARTIAL)** | Only complete for CIVIX-001–003 |
| `EVIDENCE_MANIFEST_PART2.md` | Evidence specs for CIVIX-004 through CIVIX-055 (52 cases × 15 items) | **CANONICAL** | Completes the Evidence Manifest |
| `LOCATIONS_SPATIAL_MANIFEST.md` | PostGIS coordinates for all crime scenes, cameras, towers, police stations | **CANONICAL** | Spatial ingestion authority |
| `XGBOOST_FEATURE_SPEC.md` | XGBoost behavioral feature schema, valid ranges, scoring logic | **CANONICAL** | ML model consistency authority |
| `POSTGRES_INGESTION_SPEC.md` | SQL table mappings, FK ordering, UUID rules, enum mappings | **CANONICAL** | Database seeding authority |
| `DEMO_RUNBOOK.md` | Click-by-click judge demo script for 12 Hero Cases, 15 minutes | **CANONICAL** | SIH 2026 presentation authority |
| `ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md` | Overall execution playbook | **CANONICAL (SUPERSEDED IN PARTS)** | Where conflicts exist, this index governs |
| `README.md` | Directory navigator | SUPPLEMENTARY | Navigation only |

---

## 2. RETIRED DUPLICATE DECLARATION

> [!CAUTION]
> `01_Universe_Bible_Part1.md` and `CIVIX_2.0_UNIVERSE_BIBLE_V4.md` are **byte-for-byte identical** files (MD5 hash: `A602DE3A8F767D9359708641EF6AA30E`).

**Resolution:**
- **`01_Universe_Bible_Part1.md`** → **CANONICAL.** All future edits and references use this filename.
- **`CIVIX_2.0_UNIVERSE_BIBLE_V4.md`** → **DEPRECATED.** Retained only for audit trail. No new work references this file.

Any script, seeder, or agent that reads universe specifications **must read `01_Universe_Bible_Part1.md`**, not the V4 variant.

---

## 3. CASE COUNT RESOLUTION (50 vs. 55)

> [!IMPORTANT]
> **The canonical case count is 55.** The number 50 is a legacy draft error.

**Evidence of the conflict:**
- `CIVIX_2.0_CASES_EVIDENCE_MANIFEST.md` header reads: *"50 Cases × 15 Evidence Items = 750 Evidence Specifications"*
- `ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md` line 35: references *"CIVIX-050 (or CIVIX-055 if using 55-case variant)"*
- `ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md` line 18: *"CONFLICT DETECTED: Files contain inconsistency in case count (50 vs. 55)"*

**Resolution (final, irrevocable):**
- Canonical case count: **55** (CIVIX-001 through CIVIX-055)
- Networks: N1 (001–009), N2 (010–018), N3 (019–026), N4 (027–035), N5 (036–043), N6 (044–050), N7 (051–055)
- All seeding scripts, loops, and data manifests must iterate from 1 to 55
- The Evidence Manifest header "50 Cases × 15 Items" is superseded by: **55 cases × 15 items = 825 evidence artifact specifications** (780 in Part 2 + 45 already in the original file for cases 001–003)

---

## 4. CANONICAL ID CONVENTIONS

All IDs across all files must use exactly these formats. Any legacy variant is retired.

### 4.1 — Evidence ID Format
**Canonical:** `EVD-{CASE_ID_3DIGIT}-{SEQ_3DIGIT}`

Examples: `EVD-001-001`, `EVD-027-015`, `EVD-055-008`

| Legacy Format | Status | Resolution |
|:---|:---|:---|
| `EVD-CHAINA-1` | **RETIRED** | Use `EVD-{NNN}-{NNN}` |
| `EVD-HERO-1A` | **RETIRED** | Use `EVD-{NNN}-{NNN}` |
| `EVD-H01-001` | **RETIRED** | Use `EVD-{NNN}-{NNN}` |
| `EVD-H04-004` | **RETIRED** | Where referenced in case matrix, the canonical form is the sequential ID in the Evidence Manifest |

### 4.2 — Person ID Format
**Canonical:** `P{4DIGIT}` zero-padded

Valid range: `P0001` through `P0320`
Examples: `P0001`, `P0095`, `P0320`

### 4.3 — Organization ID Format
**Canonical:** `ORG-{3DIGIT}`

Valid range: `ORG-001` through `ORG-095`
Examples: `ORG-001`, `ORG-031`, `ORG-095`

### 4.4 — Vehicle ID Format
**Canonical:** `V{4DIGIT}` zero-padded

Valid range: `V0001` through `V0160`
Examples: `V0001`, `V0047`, `V0160`

### 4.5 — Telecom SIM ID Format
**Canonical:** `T{4DIGIT}` zero-padded

Valid range: `T0001` through `T0380`
Examples: `T0001`, `T0011`, `T0073`

### 4.6 — Investigative Lead ID Format
**Canonical:** `LEAD-{3DIGIT}`

Valid range: `LEAD-001` through `LEAD-045`
Examples: `LEAD-001`, `LEAD-004`, `LEAD-031`

### 4.7 — Hypothesis ID Format
**Canonical:** `H-{CASE_ID_3DIGIT}-{LETTER}`

Examples: `H-001-A`, `H-036-B`, `H-046-A`

### 4.8 — Identity Candidate ID Format
**Canonical:** `IC-{3DIGIT}`

Valid range: `IC-001` through `IC-028`
Examples: `IC-001`, `IC-015`, `IC-022`

### 4.9 — Event ID Format
**Canonical:** `EVENT-{3DIGIT}`

Examples: `EVENT-001`, `EVENT-140`, `EVENT-202`

### 4.10 — Camera ID Format
**Canonical:** `CAM-{2DIGIT}`

Valid range: `CAM-01` through `CAM-25`

### 4.11 — Cell Tower ID Format
**Canonical:** `TOWER-{ZONE_CODE}-{2DIGIT}`

Zone codes: `DW` (Dwarka), `NH` (NH-48 Corridor), `NJ` (Najafgarh), `RH` (Rohini), `SD` (South Delhi), `GN` (Greater Noida), `KG` (Karol Bagh), `CD` (Chandni Chowk)

---

## 5. EVIDENCE TYPE ENUM (COMPLETE LIST)

All evidence types used across all manifests must be exactly one of these values:

| Enum Value | Description |
|:---|:---|
| `FIR_PDF` | First Information Report or equivalent case opening document |
| `CCTV_CLIP` | Surveillance video clip (MP4) or still frame |
| `ANPR_CROP` | Automatic Number Plate Recognition detection image |
| `AFIS_FINGERPRINT` | AFIS/10-print fingerprint card or latent print report |
| `CDR_DUMP` | Call Detail Record CSV or extract |
| `INTERROGATION_TRANSCRIPT` | Interrogation transcript, witness statement, or police notes |
| `BANK_SAR` | Bank Suspicious Activity Report |
| `FORENSIC_AUDIT` | Forensic lab report (ballistics, DNA, document analysis, etc.) |
| `LAND_REGISTRY` | Property registration document, sale deed, mutation record |
| `FINANCIAL_STATEMENT` | Bank statement, account analysis, fund flow report |
| `PHONE_RECORD` | Phone extraction report, WhatsApp export, SIM records |
| `CUSTOMS_FORM` | Customs seizure report, import/export declaration |
| `VEHICLE_SEIZURE` | Vehicle seizure report, RC document, ANPR record |
| `CONFESSION_AFFIDAVIT` | Signed confession, affidavit, or plea agreement |
| `CORONER_REPORT` | Postmortem or medical examiner report |
| `DIGITAL_FORENSICS` | Digital device forensic extraction report |
| `BALLISTICS_REPORT` | Ballistics lab analysis of firearms or ammunition |
| `WITNESS_STATEMENT` | Third-party witness statement |
| `COURT_ORDER` | Conviction order, remand order, bail order, judgment |
| `MEDICAL_REPORT` | Medical examination, injury report, GSR test result |
| `INTELLIGENCE_REPORT` | CIVIX auto-generated lead, hypothesis scoring, graph analysis output |

---

## 6. RESOLUTION OF ANTIGRAVITY GUIDE OUTSTANDING GAPS

The `ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md` references two files not yet created at the time of writing. Both are now created:

| Referenced In Guide | File Created | Status |
|:---|:---|:---|
| Phase 6.1: *"Run POSTGRES_INGESTION_SPEC.md SQL scripts (when created)"* | `POSTGRES_INGESTION_SPEC.md` | ✅ CREATED |
| Final line: *"Proceed to LOCATIONS_SPATIAL_MANIFEST.md once this phase completes."* | `LOCATIONS_SPATIAL_MANIFEST.md` | ✅ CREATED |

---

## 7. PERSON ID CROSSWALK — KNOWN ALIAS CONFLICTS

The Evidence Manifest (early draft, CIVIX-001 through CIVIX-003) and the case matrix use slightly different person descriptions for the same IDs. Canonical resolution:

| Person ID | Canonical Name | Legacy/Alias in Older Drafts | Canonical Status |
|:---|:---|:---|:---|
| P0001 | Suresh Valmiki aka "Suri Bhai" | "Rakesh Yadav" (in CIVIX-003 interrogation context — referring to same person under different name claim) | P0001 = Suresh Valmiki. "Rakesh Yadav" is an alias used in EVD-003-014 interrogation. |
| P0127 | Vinod Sabharwal | Appears as "P0127" in both CIVIX-001 and CIVIX-048 (Kamal Yadav). NOTE: P0127 in CIVIX-001 = Vinod Sabharwal; P0127 in CIVIX-048 = **Kamal Yadav** — these are TWO DIFFERENT persons sharing the same ID due to a draft numbering error. **Resolution: Kamal Yadav in CIVIX-048 is reassigned P0167.** All evidence referencing CIVIX-048 uses P0167 for Kamal Yadav. |
| P0057 | Rajesh Sharma (truck driver, CIVIX-023 convicted) | Also appears as RC Broker "Ramu" alias in CIVIX-024. NOTE: P0053 in CIVIX-023 = Rajesh Sharma (convicted truck driver); P0057 in CIVIX-024 = "Ramu" the RC Broker. These are different persons. P0057 in CIVIX-024 context = **RC Broker Ramu only**. |
| P0200 | Ratan Lal Sharma (Notary — HERO-06 false positive) | Referenced without ID in some evidence manifest drafts as "Notary FP." Canonical ID: P0200. |

---

## 8. EVIDENCE ID CROSSWALK — LEGACY TO CANONICAL

Where legacy evidence IDs appear in older narrative sections, resolve to canonical:

| Legacy ID | Canonical ID | Case | Description |
|:---|:---|:---|:---|
| `EVD-H01-001` | `EVD-001-001` | CIVIX-001 | FIR, Dwarka PS 2012 |
| `EVD-H04-004` | `EVD-044-002` | CIVIX-044 | Financial audit — robbery proceeds to Yadav Properties |
| `EVD-CHAINA-1` | `EVD-001-008` | CIVIX-001 | CDR Dump, burner phone |
| `EVD-HERO-1A` | `EVD-027-001` | CIVIX-027 | Interrogation transcript, "Vikram @ Pandit" mention |

---

## 9. RECOMMENDED READING & EXECUTION ORDER

For any agent, engineer, or executor entering the Presentation Universe:

### Documentation Reading Order
1. `00_INDEX_AND_CANONICAL_VERSIONS.md` ← **You are here**
2. `01_Universe_Bible_Part1.md` — universe design and Hero Cases overview
3. `02_Universe_Bible_Part2_CaseMatrix.md` — all 55 case specifications
4. `CIVIX_2.0_UNIVERSE_BIBLE_PART_3.md` — entity rosters
5. `XGBOOST_FEATURE_SPEC.md` — behavioral model definitions
6. `CIVIX_2.0_PERSONS_PHOTO_MANIFEST.md` — photo generation rules

### Materialization Execution Order
1. `LOCATIONS_SPATIAL_MANIFEST.md` — prepare PostGIS geometries
2. `POSTGRES_INGESTION_SPEC.md` — understand schema mappings and FK ordering
3. `ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md` — run the seeding pipeline
4. `CIVIX_2.0_CASES_EVIDENCE_MANIFEST.md` + `EVIDENCE_MANIFEST_PART2.md` — generate all 825 evidence artifacts
5. `CIVIX_2.0_PERSONS_PHOTO_MANIFEST.md` — generate person photos

### Demo Presentation Order
1. `DEMO_RUNBOOK.md` — follow click-by-click script for SIH 2026

---

## 10. ISOLATION & CRASH PROTECTION DECLARATION

> [!CAUTION]
> All Presentation Universe materialization MUST occur in an isolated namespace.

**Rules:**
- PostgreSQL schema: `civix_presentation` (separate from `civix_demo` and `civix_verify`)
- Seeding run identifier: `generation_run_id = 'SIH2026_DEMO_V1'`
- Neo4j database: `civix_presentation_graph` (separate from `civix_demo_graph`)
- The `civix_demo` database (containing the Golden World) must remain completely untouched
- The `civix_verify` schema must remain completely untouched
- If the presentation universe seeder fails for any reason, `civix_demo` is unaffected

---

*Last Updated: 2026-09-04 | Authority: CIVIX 2.0 Presentation Universe Governance | Supersedes all prior conflict notes in `ANTIGRAVITY_EXECUTION_GUIDE_v1.0.md`*
