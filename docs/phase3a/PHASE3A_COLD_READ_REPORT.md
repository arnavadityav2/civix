# PHASE 3A: COLD READ & DATASET AUDIT REPORT
**Target:** Profile C (Machine Learning Intelligence Pipeline)
**Date:** 2026-08-29

## 1. Architecture & Schema Reconciliation
I have cold-read the architecture documents, including `03_DATABASE_SCHEMA_BIBLE.md`, the Golden World specs, the Phase 2A migrations, and the Phase 2B synthetic data specs.

**The Golden World / Postgres Schema:** Contains 80 highly normalized tables designed for investigative workflows, forensics, chain-of-custody, and UI audit logging.
**Profile C ML Dataset:** Contains 13 physical Parquet directories representing the high-volume behavioral subset of the schema (Persons, Organisations, Phones, SIMs, Devices, Locations, Cell Sectors, Accounts, CDRs, Transactions, Cases, Case Roles, plus Ground Truth).

**Conflict Check:** There are ZERO conflicts. Profile C is a perfect, optimized, denormalized subset of the canonical schema designed specifically for out-of-core tensor ingestion.

## 2. Actual Available Data (Profile C)
Based on programmatic inspection of `D:\civix_data\synthetic\profile_c`:

| Entity / Event | Actual Rows | Core Attributes Available |
|----------------|-------------|---------------------------|
| **CDRs** | 75,000,000 | `caller_phone_id`, `callee_phone_id`, `timestamp`, `duration_seconds`, `call_type`, `cell_sector_id` |
| **Transactions** | 18,385,110 | `sender_account_id`, `receiver_account_id`, `amount`, `currency`, `timestamp`, `transaction_type` |
| **Persons** | 250,000 | `person_id`, `gender`, `occupation`, `date_of_birth` |
| **Locations** | 15,000 | `latitude`, `longitude`, `region` |
| **Cell Sectors** | 8,000 | `centroid_latitude`, `centroid_longitude`, `azimuth_degrees` |
| **Phones/SIMs/Devs**| 1.2M total | `operator`, `is_burner`, `device_type` |
| **Cases** | 25,000 | `case_type`, `priority`, `status` |

## 3. Actual Ground Truth & Splitting
- **Splits:** Pre-stratified perfectly (`TRAIN`: 175,000 | `VALIDATION`: 37,500 | `TEST`: 37,500).
- **Labels:** The dataset strictly isolates ground truth in `ground_truth/person_labels/*.parquet`.
- **Scenarios:** 
  - `normal`: 175,000 (~70%)
  - `suspicious`: 37,500 (~15%)
  - `confirmed_pattern`: 25,000 (~10%)
  - `false_positive`: 12,500 (~5%)

## 4. Leakage & Temporal Audit
- **Label Leakage:** An automated scan confirmed that ZERO columns containing `scenario`, `risk_score`, or `is_positive` have leaked into the core feature tables.
- **Temporal Leakage:** All 93.3 million events (CDRs/Transactions) contain explicit `timestamp` fields bounding activity between 2022-01-01 and 2024-12-31.
- **Action Required:** Feature engineering MUST implement an `as_of_timestamp` parameter to filter out future events during historical point-in-time predictions.

## 5. Computational Constraints
- **Hardware:** Dell G15.
- **Constraint:** We cannot load 75M CDRs into Pandas/RAM.
- **Mitigation:** We will use DuckDB for all feature aggregations and PyArrow dataset streaming for model ingestion. We will strictly adhere to the 100,000 record batch limit.

## 6. Graph Relationships Supported
The data natively supports a massive heterogeneous graph:
- `Person` -> [OWNS] -> `Phone` / `SIM` / `Device` / `Account`
- `Phone` -> [CALLED] -> `Phone` (Temporal Edge via CDR)
- `Account` -> [TRANSFERRED] -> `Account` (Temporal Edge via Txn)
- `Person` -> [LOCATED_AT] -> `Cell Sector` (via CDR)
- `Person` -> [INVOLVED_IN] -> `Case`
