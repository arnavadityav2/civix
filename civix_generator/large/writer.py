"""
CIVIX Large-Scale Generator: Streaming Parquet Writer
civix_generator/large/writer.py

Handles sharded Parquet writes with rotation and integrity checking.
Never holds more than one shard worth of records in RAM.
"""
from __future__ import annotations
import os
import hashlib
from typing import List, Dict, Any, Optional
import pyarrow as pa
import pyarrow.parquet as pq


class ShardWriter:
    """Writes records to Parquet shards with automatic rotation.

    Usage:
        writer = ShardWriter(base_dir, entity_type="cdr",
                             partition_keys=["year", "month"],
                             shard_rows=1_000_000)
        for batch in generate():
            writer.write_batch(batch)
        stats = writer.close()
    """

    def __init__(
        self,
        base_dir: str,
        entity_type: str,
        partition_keys: Optional[List[str]] = None,
        shard_rows: int = 1_000_000,
        compression: str = "snappy",
    ):
        self.base_dir = base_dir
        self.entity_type = entity_type
        self.partition_keys = partition_keys or []
        self.shard_rows = shard_rows
        self.compression = compression

        self._buffer: List[Dict[str, Any]] = []
        self._shard_index = 0
        self._total_rows = 0
        self._files_written: List[Dict[str, Any]] = []

        # Current shard partition values (for hive directory naming)
        self._current_partition: Dict[str, Any] = {}

    # ── Public API ───────────────────────────────────────────────────────────

    def write_batch(self, records: List[Dict[str, Any]]) -> None:
        """Buffer records and flush shards as they fill."""
        if not records:
            return

        # Group by partition key values (for hive partitioning)
        if self.partition_keys:
            groups = self._group_by_partition(records)
        else:
            groups = {(): records}

        for pkey_vals, group_records in groups.items():
            self._buffer.extend(group_records)
            partition_dict = dict(zip(self.partition_keys, pkey_vals))

            while len(self._buffer) >= self.shard_rows:
                shard = self._buffer[:self.shard_rows]
                self._buffer = self._buffer[self.shard_rows:]
                self._flush_shard(shard, partition_dict)

    def flush(self) -> None:
        """Force-write whatever is remaining in the buffer."""
        if self._buffer:
            self._flush_shard(self._buffer, self._current_partition)
            self._buffer = []

    def close(self) -> Dict[str, Any]:
        """Flush remaining buffer and return summary statistics."""
        self.flush()
        return {
            "entity_type": self.entity_type,
            "total_rows": self._total_rows,
            "shards": len(self._files_written),
            "files": self._files_written,
        }

    # ── Internal ─────────────────────────────────────────────────────────────

    def _group_by_partition(
        self, records: List[Dict[str, Any]]
    ) -> Dict[tuple, List[Dict[str, Any]]]:
        groups: Dict[tuple, List[Dict[str, Any]]] = {}
        for rec in records:
            key = tuple(rec.get(k) for k in self.partition_keys)
            groups.setdefault(key, []).append(rec)
        return groups

    def _flush_shard(
        self,
        records: List[Dict[str, Any]],
        partition: Dict[str, Any],
    ) -> None:
        if not records:
            return

        # Build hive directory path
        parts = []
        for k, v in partition.items():
            parts.append(f"{k}={v}")
        rel_dir = os.path.join(self.entity_type, *parts) if parts else self.entity_type
        out_dir = os.path.join(self.base_dir, rel_dir)
        os.makedirs(out_dir, exist_ok=True)

        # Remove partition keys from column data (they live in the path)
        clean_records = []
        for rec in records:
            clean = {k: v for k, v in rec.items() if k not in self.partition_keys}
            clean_records.append(clean)

        shard_filename = f"part-{self._shard_index:05d}.parquet"
        shard_path = os.path.join(out_dir, shard_filename)

        table = pa.Table.from_pylist(clean_records)
        pq.write_table(table, shard_path, compression=self.compression)

        # Checksum
        sha256 = _sha256_file(shard_path)
        size_bytes = os.path.getsize(shard_path)

        self._files_written.append({
            "path": shard_path,
            "rows": len(records),
            "bytes": size_bytes,
            "sha256": sha256,
            "partition": partition,
            "shard_index": self._shard_index,
        })

        self._total_rows += len(records)
        self._shard_index += 1
        self._current_partition = partition


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
