"""
CIVIX Synthetic World V2: Memory-Bounded Streaming Parquet Writer
civix_generator/v2/streaming_writer.py

Writes Parquet shards without holding more than one batch in RAM.
Uses PyArrow write_to_dataset for efficient schema-enforced output.
"""
from __future__ import annotations
import json
import os
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

import pyarrow as pa
import pyarrow.parquet as pq


class ShardWriter:
    """
    Accepts streaming record batches and writes them to sharded Parquet files.

    Usage:
        with ShardWriter(out_dir, schema, shard_rows=500_000) as writer:
            for batch in generator():
                writer.write(batch)
    """

    def __init__(
        self,
        out_dir: Path,
        schema: pa.Schema,
        shard_rows: int = 500_000,
        partition_cols: Optional[List[str]] = None,
    ):
        self.out_dir       = Path(out_dir)
        self.schema        = schema
        self.shard_rows    = shard_rows
        self.partition_cols = partition_cols or []

        self.out_dir.mkdir(parents=True, exist_ok=True)

        self._shard_idx    = 0
        self._row_count    = 0
        self._total_rows   = 0
        self._buffer: List[Dict[str, Any]] = []
        self._writer: Optional[pq.ParquetWriter] = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def write(self, records: List[Dict[str, Any]]) -> None:
        self._buffer.extend(records)
        while len(self._buffer) >= self.shard_rows:
            self._flush_shard(self._buffer[:self.shard_rows])
            self._buffer = self._buffer[self.shard_rows:]

    def close(self) -> None:
        if self._buffer:
            self._flush_shard(self._buffer)
            self._buffer = []

    def _flush_shard(self, records: List[Dict[str, Any]]) -> None:
        if not records:
            return
        table = _records_to_table(records, self.schema)
        shard_path = self.out_dir / f"shard_{self._shard_idx:05d}.parquet"
        pq.write_table(
            table,
            shard_path,
            compression="snappy",
            write_statistics=True,
        )
        self._total_rows += len(records)
        self._shard_idx  += 1

    @property
    def total_rows(self) -> int:
        return self._total_rows + len(self._buffer)


def _records_to_table(records: List[Dict[str, Any]], schema: pa.Schema) -> pa.Table:
    """Convert a list of dicts to a PyArrow Table matching the given schema."""
    columns: Dict[str, List[Any]] = {field.name: [] for field in schema}
    for rec in records:
        for field in schema:
            val = rec.get(field.name, None)
            columns[field.name].append(val)
    arrays = [pa.array(columns[field.name], type=field.type) for field in schema]
    return pa.table(arrays, schema=schema)


def write_manifest(
    out_dir: Path,
    generation_config: Dict[str, Any],
    artifact_summary: Dict[str, Any],
) -> None:
    """Write manifest.json, generation_config.json, and checksums.json."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "generation_config.json", "w") as f:
        json.dump(generation_config, f, indent=2, default=str)

    manifest = {
        "generator_version":  "civix-v2-2.0.0",
        "generated_at":       time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "artifacts":          artifact_summary,
        "schema_version":     "v2",
    }
    with open(out_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    # Compute file checksums for determinism verification
    checksums = {}
    for name, info in artifact_summary.items():
        dir_path = out_dir / name
        if dir_path.is_dir():
            file_checksums = {}
            for fpath in sorted(dir_path.rglob("*.parquet")):
                with open(fpath, "rb") as fh:
                    digest = hashlib.sha256(fh.read()).hexdigest()
                file_checksums[str(fpath.name)] = digest
            checksums[name] = file_checksums

    with open(out_dir / "checksums.json", "w") as f:
        json.dump(checksums, f, indent=2)
