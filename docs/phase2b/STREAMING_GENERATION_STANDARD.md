# CIVIX — STREAMING GENERATION & RAM SAFETY STANDARD
**Version**: 1.0 | **Date**: 2026-08-29

## 1. RAM Bounding Requirements
To ensure the generator runs safely on a memory-constrained Dell G15 laptop (or a cheap cloud VM), the generator MUST NOT materialize the entire world state in Python dictionaries.

- **Maximum Python Heap**: 2 GB
- **Batch Size Limit**: 100,000 records per flush.

## 2. Streaming Generator Architecture

Instead of `generate_cdrs() -> List[Dict]`, generators must be implemented as Python generators yielding batches:

```python
def generate_cdrs(population_index: Iterable, config: Config) -> Iterator[List[Dict]]:
    buffer = []
    for person in population_index:
        for cdr in generate_person_cdrs(person, config):
            buffer.append(cdr)
            if len(buffer) >= config.flush_size:
                yield buffer
                buffer = []
    if buffer:
        yield buffer
```

## 3. Canonical Format: Parquet
For large-scale data (Profiles B, C, D), flat CSV and JSONL are extremely inefficient for both disk I/O and storage.

- **Primary Output Format**: `Apache Parquet` via `pyarrow` or `pandas`.
- **Why?**: Columnar storage compresses highly repetitive data (like cell tower IDs, transaction types) by 80-90%. It is the native format for DuckDB, Spark, and modern ML pipelines.
- **Fallback Format**: `JSONL` will be generated *only* for Profile A (Development) to allow easy human inspection of the records.

## 4. Chunked File Writes
A single 75M row CDR Parquet file is difficult to process. The writer must rotate files:
`cdr_shard_0000.parquet` -> `cdr_shard_0001.parquet` (Rotated every 1M rows).

## 5. Garbage Collection Strategy
- Variables holding large intermediate lists must be explicitly `del`'d or allowed to fall out of scope immediately after yielding.
- The `population_index` (mapping person UUIDs to basic traits) is the only object kept in memory for the duration of the run. It contains minimal fields (ID, age_group, risk_score) to keep memory < 500MB even for 1M persons.
