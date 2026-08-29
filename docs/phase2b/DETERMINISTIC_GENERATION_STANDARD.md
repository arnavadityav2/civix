# CIVIX — DETERMINISTIC GENERATION STANDARD
**Version**: 1.0 | **Date**: 2026-08-29

## 1. Absolute Reproducibility Rule
The exact same `seed + profile + generator_version` MUST yield the exact same logical dataset, regardless of whether it is generated locally on a laptop or distributed across 50 cloud nodes.

## 2. Seed Hierarchy
Never use global random states (`numpy.random.seed()`). Use explicit Generator objects initialized with a hierarchical seed.

```python
from numpy.random import Generator, PCG64

master_seed = 20260829
run_seed = hash(f"{master_seed}_{run_id}")

# Domain-specific streams
rng_population = Generator(PCG64(run_seed + 1))
rng_telecom    = Generator(PCG64(run_seed + 2))
rng_financial  = Generator(PCG64(run_seed + 3))

# Entity-specific streams (for parallel generation without ordering bugs)
def get_person_rng(person_id: str) -> Generator:
    person_seed = hash(f"{run_seed}_{person_id}")
    return Generator(PCG64(person_seed))
```

## 3. Stable UUID Generation
Do not use `uuid4()`. All UUIDs must be deterministically derived from their domain and unique index/keys.

```python
import hashlib, uuid

def make_uuid(domain: str, *keys) -> str:
    key_str = domain + "|" + "|".join(str(k) for k in keys)
    return str(uuid.UUID(hashlib.md5(key_str.encode()).hexdigest()))

# Stable across runs:
p1_id = make_uuid("person", master_seed, person_index)
cdr_id = make_uuid("cdr", master_seed, caller_id, timestamp)
```

## 4. Manifest Requirement
Every generation run creates a `manifest.json` containing:
- `generator_version` (git commit hash)
- `schema_version`
- `master_seed`
- `profile_name`
- `shard_count`
- `record_counts` (exact row counts per entity type)
- `checksums` (SHA-256 for all generated files)
- `generation_timestamp`

If the manifest does not match, the dataset is considered corrupt.
