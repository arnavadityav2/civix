"""
CIVIX Large-Scale Generator: Checkpointing
civix_generator/large/checkpoint.py

Tracks which stages have completed so that --resume works
without re-generating or duplicating data.
"""
from __future__ import annotations
import json
import os
import time
from typing import Dict, Any, Set


class Checkpoint:
    """Simple JSON-backed checkpoint store.

    Stages that have been committed are idempotent:
    the engine skips them on --resume.

    Schema of checkpoint.json:
    {
        "profile": "C",
        "seed": 20260829,
        "started_at": 1724900000,
        "completed_stages": ["entities", "telecom", "finance"],
        "shard_progress": {
            "cdr": 45,          # last completed shard index
            "transaction": 12
        },
        "row_counts": {
            "person": 250000,
            "device": 375000,
            ...
        }
    }
    """

    def __init__(self, checkpoint_path: str):
        self.path = checkpoint_path
        self._state: Dict[str, Any] = {}
        self._load()

    # ── Stage management ──────────────────────────────────────────────────────

    @property
    def completed_stages(self) -> Set[str]:
        return set(self._state.get("completed_stages", []))

    def stage_done(self, stage: str) -> bool:
        return stage in self.completed_stages

    def mark_stage_done(self, stage: str, rows: int = 0) -> None:
        stages = self._state.setdefault("completed_stages", [])
        if stage not in stages:
            stages.append(stage)
        self._state.setdefault("row_counts", {})[stage] = rows
        self._save()

    # ── Shard-level progress ──────────────────────────────────────────────────

    def last_shard(self, entity_type: str) -> int:
        """Return the last fully-written shard index (-1 if none)."""
        return self._state.get("shard_progress", {}).get(entity_type, -1)

    def update_shard(self, entity_type: str, shard_index: int) -> None:
        self._state.setdefault("shard_progress", {})[entity_type] = shard_index
        self._save()

    # ── Initialization ────────────────────────────────────────────────────────

    def initialize(self, profile: str, seed: int) -> None:
        """Called once at the start of a fresh generation run."""
        if not self._state:
            self._state = {
                "profile": profile,
                "seed": seed,
                "started_at": int(time.time()),
                "completed_stages": [],
                "shard_progress": {},
                "row_counts": {},
            }
            self._save()

    def is_fresh(self) -> bool:
        return not bool(self._state)

    def summary(self) -> Dict[str, Any]:
        return dict(self._state)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if os.path.exists(self.path):
            with open(self.path, "r", encoding="utf-8") as f:
                self._state = json.load(f)

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self._state, f, indent=2)
