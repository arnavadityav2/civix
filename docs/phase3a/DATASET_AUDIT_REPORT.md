# PHASE 3A-01: DATASET AUDIT REPORT
**Profile Audited:** Profile C
**Path:** `D:\civix_data\synthetic\profile_c`
**Timestamp:** 2026-08-29T05:00:05.607590Z

## 1. Dataset Inventory & Row Counts
Total logical tables found: 13

| Table | Row Count | Attributes | Key File Path |
|-------|-----------|------------|---------------|
| `accounts` | 225,000 | 8 | `accounts/` |
| `case_entity_roles` | 112,855 | 4 | `case_entity_roles/` |
| `cases` | 25,000 | 8 | `cases/` |
| `cell_sectors` | 8,000 | 9 | `cell_sectors/` |
| `devices` | 375,000 | 5 | `devices/` |
| `ground_truth/person_labels` | 250,000 | 12 | `ground_truth/person_labels/` |
| `ground_truth/train_val_test_split` | 250,000 | 4 | `ground_truth/train_val_test_split/` |
| `locations` | 15,000 | 7 | `locations/` |
| `ml_features` | 500,000 | 21 | `ml_features/` |
| `organisations` | 10,000 | 4 | `organisations/` |
| `persons` | 250,000 | 11 | `persons/` |
| `phones` | 450,000 | 5 | `phones/` |
| `sims` | 450,000 | 4 | `sims/` |

## 2. Table Schemas & Missingness
### `accounts`
- `account_id` (Null rate: 0.00%)
- `account_index` (Null rate: 0.00%)
- `bank` (Null rate: 0.00%)
- `account_type` (Null rate: 0.00%)
- `masked_number` (Null rate: 0.00%)

### `case_entity_roles`
- `cer_id` (Null rate: 0.00%)
- `case_id` (Null rate: 0.00%)
- `person_id` (Null rate: 0.00%)
- `role` (Null rate: 0.00%)

### `cases`
- `case_id` (Null rate: 0.00%)
- `case_index` (Null rate: 0.00%)
- `case_type` (Null rate: 0.00%)
- `status` (Null rate: 0.00%)
- `priority` (Null rate: 0.00%)

### `cell_sectors`
- `cell_id` (Null rate: 0.00%)
- `location_type` (Null rate: 0.00%)
- `centroid_latitude` (Null rate: 0.00%)
- `centroid_longitude` (Null rate: 0.00%)
- `azimuth_degrees` (Null rate: 0.00%)

### `devices`
- `device_id` (Null rate: 0.00%)
- `device_index` (Null rate: 0.00%)
- `imei` (Null rate: 0.00%)
- `brand` (Null rate: 0.00%)
- `device_type` (Null rate: 0.00%)

### `ground_truth/person_labels`
- `entity_id` (Null rate: 0.00%)
- `entity_type` (Null rate: 0.00%)
- `person_index` (Null rate: 0.00%)
- `scenario_class` (Null rate: 0.00%)
- `scenario_family` (Null rate: 0.00%)

### `ground_truth/train_val_test_split`
- `entity_id` (Null rate: 0.00%)
- `person_index` (Null rate: 0.00%)
- `split` (Null rate: 0.00%)
- `active_start_day` (Null rate: 0.00%)

### `locations`
- `location_id` (Null rate: 0.00%)
- `location_type` (Null rate: 0.00%)
- `latitude` (Null rate: 0.00%)
- `longitude` (Null rate: 0.00%)
- `uncertainty_radius_meters` (Null rate: 0.00%)

### `ml_features`
- `person_id` (Null rate: 0.00%)
- `total_calls` (Null rate: 50.00%)
- `avg_call_duration_sec` (Null rate: 50.00%)
- `std_call_duration_sec` (Null rate: 50.00%)
- `unique_callees` (Null rate: 50.00%)

### `organisations`
- `org_id` (Null rate: 0.00%)
- `org_index` (Null rate: 0.00%)
- `name` (Null rate: 0.00%)
- `org_type` (Null rate: 0.00%)

### `persons`
- `person_id` (Null rate: 0.00%)
- `person_index` (Null rate: 0.00%)
- `full_name` (Null rate: 0.00%)
- `gender` (Null rate: 0.00%)
- `date_of_birth` (Null rate: 0.00%)

### `phones`
- `phone_id` (Null rate: 0.00%)
- `phone_index` (Null rate: 0.00%)
- `number` (Null rate: 0.00%)
- `operator` (Null rate: 0.00%)
- `is_recycled` (Null rate: 0.00%)

### `sims`
- `sim_id` (Null rate: 0.00%)
- `sim_index` (Null rate: 0.00%)
- `iccid` (Null rate: 0.00%)
- `is_burner` (Null rate: 0.00%)

