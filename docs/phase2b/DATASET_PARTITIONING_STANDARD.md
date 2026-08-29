# CIVIX — DATASET PARTITIONING STANDARD
**Version**: 1.0 | **Date**: 2026-08-29

## 1. Storage Layout Structure
The generated dataset in Object Storage (or local disk) follows a strict hive-partitioned directory structure to allow partial loading, subset analysis, and localized regeneration.

```text
output/
  runs/
    run_{YYYYMMDD_HHMMSS}_{profile}/
      manifest.json
      config_dump.yaml
      ground_truth/
        entity_type=person_relationships/
          part-0000.parquet
        entity_type=case_labels/
          part-0000.parquet
      data/
        entity_type=person/
          part-0000.parquet
        entity_type=cdr/
          year=2024/
            month=01/
              part-0000.parquet
              part-0001.parquet
            month=02/
              part-0000.parquet
```

## 2. Partitioning Dimensions

| Entity Class | Primary Partition | Secondary Partition | Shard Size Limit |
|---|---|---|---|
| Master Entities (Persons, Accounts) | `entity_type` | None | 500,000 rows |
| Low-volume Events (Cases, Property Tx) | `entity_type` | None | 500,000 rows |
| High-volume Events (CDRs, Transactions) | `entity_type` | `year` -> `month` | 1,000,000 rows |
| Ground Truth (Labels) | `entity_type` | None | 100,000 rows |

## 3. Operational Advantages
- **Targeted Training**: If ML researchers only want to train a model on 2024 financial data, they read `data/entity_type=transaction/year=2024/*.parquet` directly.
- **Partial Ingestion**: If testing database RLS rules, developers can choose to only ingest the first shard of persons and cases, completely skipping the heavy CDR data.
- **Safe Deletion**: Data lifecycle rules can easily delete older runs or specific months without complex database queries.
