# 04 — Data Model & Ontology
**Version**: 1.0 | **Date**: 2026-08-29

## 1. The Universal Entity Hierarchy

Every domain object in CIVIX is a subtype of `civix.entity`. The entity supertype provides:
- A single FK target for all polymorphic relationships
- A discriminator (`entity_type`) for runtime dispatch
- A shared UUID namespace across all domain types

```
civix.entity (supertype)
├── civix.person             (canonical human — created only by identity resolution)
├── civix.source_identity    (raw identifier from data — ingest target)
├── civix.phone_number       (telecom MSISDN)
├── civix.sim                (physical SIM card by ICCID)
├── civix.device             (physical handset by IMEI)
├── civix.financial_account  (bank/UPI/wallet account)
├── civix.vehicle            (by registration number / VIN)
├── civix.property           (real estate / land — Khasra, title deed)
├── civix.organization       (company, government body, trust)
├── civix.network            (criminal / social / financial network)
└── civix.location           (PostGIS geometry — point, polygon, sector)
```

## 2. Entity Cardinalities (Golden World v2.1)

| Entity | Count | Notes |
|---|---|---|
| Persons | 55 | Includes victims, witnesses, bystanders |
| Organizations | 16 | Including front companies |
| Networks | 3 | Alpha (Drug), Beta (Land Grab), Gamma (Extortion) |
| Phone Numbers | 42 | Multiple per person; some shared |
| Devices | 11 | Includes burner phones |
| SIMs | STATUS: OPEN DECISION | Not explicitly enumerated in Golden World |
| Vehicles | 13 | Some shared across networks |
| Financial Accounts | 29 | Including joint accounts |
| Properties | 8 | Including fraudulently transferred ones |
| Locations | STATUS: OPEN DECISION | Generated from CDR cell IDs + sighting locations |

## 3. Critical Ontological Rules

### 3.1 SourceIdentity vs Person
- **SourceIdentity**: Raw identifier from data (name string, phone number, IMEI). Created during ingest. May not refer to a known canonical person.
- **Person**: Canonical human entity. Created ONLY by an explicit `IdentityResolutionDecision`. Never created automatically.

### 3.2 What is NOT an Entity
- Assertions are NOT entities (they are structured claims)
- Events are NOT entities in the entity subtype sense (they are occurrences with a separate table)
- Cases are NOT entity subtypes (they are organizational containers)
- Network membership is expressed as `assertion(MEMBER_OF)`, not a structural property of the entity

### 3.3 Temporal Independence of Device/SIM/Person
- A Person does not own a Device. A Person USED a Device during a time interval (expressed as an Assertion).
- A SIM is not permanently assigned to a Phone Number. The assignment is temporal (`sim_number_assignment`).
- A SIM is not permanently inserted in a Device. The physical presence is temporal (`sim_in_device`).
- These three relationship types have DIFFERENT constraint regimes.

### 3.4 Location Semantics
A Location is an entity. There are multiple location types:
- `EXACT_POINT`: Known precise GPS coordinate
- `ESTIMATED_POINT`: Approximate, has `uncertainty_radius_meters`
- `CELL_SECTOR_POLYGON`: Coverage area of a cell tower sector (NOT the user's precise position)
- `CCTV_COVERAGE_POLYGON`: CCTV camera coverage area
- `PROPERTY_BOUNDARY`: Cadastral boundary
- `CRIME_SCENE`: Defined scene boundary
- `GEOFENCE`: Investigative perimeter

**NEVER infer exact co-location from cell tower.**

## 4. Predicate Vocabulary Summary

See `03_DATABASE_SCHEMA_BIBLE.md` Section on ENUMs for the complete 35-predicate vocabulary.

Banned predicates: `ASSOCIATED_WITH`, `LINKED_TO`, `RELATED_TO` (too vague — no investigative meaning).

## 5. Network Structure (Golden World)

```
Network Alpha (Drug, Jaipur–Ajmer)     Network Beta (Land Grab, Ajmer–Pushkar)
Vikram P-01 ─── Amit P-02             Harish P-09 ─── Neha P-08
  │               │                       │               │
Priya P-05     Suresh P-03            Sunita P-12 ─── Rajendra P-13
  │               │                       │
Ravi P-06      Dinesh P-11            Deepak P-04
  │
Irfan P-07

Network Gamma (Extortion, Jaipur Commercial)      Hidden Cross-Network Links
Bhupendra P-10 ─── Arjun P-15              Amit P-02 ↔ Harish P-09 [shared account]
  │                    │                    Suresh P-03 → Alpha+Beta [shared vehicle]
Kavita P-17         Sanjay P-16            Ravi P-06 ↔ Bhupendra P-10 [brother-in-law]
                       │                   Babita Devi: victim of Alpha + Beta
                     Rocky P-18
```
