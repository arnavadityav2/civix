"""
CIVIX Large-Scale Generator: Manifest
civix_generator/large/manifest.py

Generates and reads manifest.json for each dataset run.
"""
from __future__ import annotations
import hashlib
import json
import os
import time
from typing import Dict, Any, List

GENERATOR_VERSION = "2.0.0"
SCHEMA_VERSION = "civix-2.1"
SCENARIO_CATALOG_VERSION = "1.0"


def build_manifest(
    profile_name: str,
    seed: int,
    config_dict: Dict[str, Any],
    file_stats: List[Dict[str, Any]],
    row_counts: Dict[str, int],
    started_at: float,
) -> Dict[str, Any]:
    """Build the complete manifest dictionary."""
    config_hash = hashlib.sha256(
        json.dumps(config_dict, sort_keys=True).encode()
    ).hexdigest()

    return {
        "dataset_version": f"profile_{profile_name.lower()}_v1",
        "generator_version": GENERATOR_VERSION,
        "schema_version": SCHEMA_VERSION,
        "scenario_catalog_version": SCENARIO_CATALOG_VERSION,
        "profile": profile_name,
        "seed": seed,
        "configuration_hash": config_hash,
        "generation_timestamp": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at)
        ),
        "generation_duration_seconds": int(time.time() - started_at),
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "files": file_stats,
        "total_files": len(file_stats),
        "total_bytes": sum(f["bytes"] for f in file_stats),
    }


def write_manifest(manifest: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return path


def read_manifest(output_dir: str) -> Dict[str, Any]:
    path = os.path.join(output_dir, "manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
