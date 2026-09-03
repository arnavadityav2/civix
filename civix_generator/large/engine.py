"""
CIVIX Large-Scale Generator: Main Engine
civix_generator/large/engine.py

Orchestrates all generation stages in the correct dependency order.
Each stage is independently checkpointed. --resume skips completed stages.

Memory budget enforcement:
  The engine monitors psutil.Process.memory_info().rss and warns if
  RAM usage exceeds 2 GB (configurable via MAX_RAM_GB).
"""
from __future__ import annotations
import dataclasses
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .config import ProfileConfig
from .seeds import SeedBank
from .checkpoint import Checkpoint
from .manifest import build_manifest, write_manifest
from .geography import generate_locations, generate_cell_sectors, build_cell_index, build_location_index
from .scenarios import assign_scenarios
from .entities import generate_persons, generate_organisations
from .telecom import generate_phones, generate_sims, generate_devices
from .telecom_fast import generate_cdrs_fast as generate_cdrs

from .finance import generate_accounts, generate_transactions
from .cases import generate_cases, generate_case_entity_roles
from .labels import generate_person_labels, generate_train_val_test_split
from .features import generate_person_behavior_features
from .writer import ShardWriter

log = logging.getLogger("civix.large")

MAX_RAM_GB = 2.0   # Warn threshold


def _check_ram():
    """Print a warning if we're approaching the RAM limit."""
    try:
        import psutil
        rss_gb = psutil.Process().memory_info().rss / (1 << 30)
        if rss_gb > MAX_RAM_GB:
            log.warning("[!] RAM usage %.2f GB exceeds %.1f GB threshold!", rss_gb, MAX_RAM_GB)
        return rss_gb
    except ImportError:
        return 0.0


class LargeScaleEngine:
    def __init__(
        self,
        config: ProfileConfig,
        output_dir: str,
        overwrite: bool = False,
        resume: bool = False,
        verbose: bool = False,
        smoke_fraction: float = 1.0,
    ):
        self.config       = config
        self.output_dir   = output_dir
        self.overwrite    = overwrite
        self.resume       = resume
        self.smoke_fraction = smoke_fraction

        level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

        # Apply smoke fraction to all counts
        if smoke_fraction < 1.0:
            self._apply_smoke(smoke_fraction)

        self.seed_bank = SeedBank(config.seed)
        ckpt_path      = os.path.join(output_dir, "checkpoint.json")
        self.ckpt      = Checkpoint(ckpt_path)
        self._started_at = time.time()
        self._file_stats: List[Dict[str, Any]] = []
        self._row_counts: Dict[str, int] = {}

    def _apply_smoke(self, frac: float):
        cfg = self.config
        cfg.persons       = max(10, round(cfg.persons * frac))
        cfg.organizations = max(5, round(cfg.organizations * frac))
        cfg.devices       = max(10, round(cfg.devices * frac))
        cfg.sims          = max(10, round(cfg.sims * frac))
        cfg.phone_numbers = max(10, round(cfg.phone_numbers * frac))
        cfg.accounts      = max(10, round(cfg.accounts * frac))
        cfg.properties    = max(10, round(cfg.properties * frac))
        cfg.vehicles      = max(10, round(cfg.vehicles * frac))
        cfg.locations     = max(5, round(cfg.locations * frac))
        cfg.cell_sectors  = max(5, round(cfg.cell_sectors * frac))
        cfg.cdrs          = max(100, round(cfg.cdrs * frac))
        cfg.transactions  = max(50, round(cfg.transactions * frac))
        cfg.cases         = max(5, round(cfg.cases * frac))

    # ── Disk pre-flight check ─────────────────────────────────────────────────

    def _check_disk(self, est_gb: float = 6.0):
        """Estimate required disk and abort if insufficient."""
        try:
            import shutil
            stat = shutil.disk_usage(self.output_dir if os.path.exists(self.output_dir) else ".")
            avail_gb = stat.free / (1 << 30)
            required_gb = est_gb * 1.2   # 20% safety margin
            log.info("Disk: %.1f GB available, ~%.1f GB required (with 20%% margin)", avail_gb, required_gb)
            if avail_gb < required_gb:
                raise RuntimeError(
                    f"Insufficient disk space: {avail_gb:.1f} GB available, "
                    f"{required_gb:.1f} GB required. Free up space and retry."
                )
        except ImportError:
            log.warning("shutil not available, skipping disk check")

    # ── Stage runner ──────────────────────────────────────────────────────────

    def _run_stage(
        self,
        stage_name: str,
        generator,
        entity_type: str,
        partition_keys: Optional[List[str]] = None,
    ) -> int:
        """Run one streaming generation stage and return the row count."""
        if self.resume and self.ckpt.stage_done(stage_name):
            rows = self.ckpt._state.get("row_counts", {}).get(stage_name, 0)
            log.info("[skip] '%s' (checkpoint: %d rows)", stage_name, rows)
            self._row_counts[stage_name] = rows
            return rows

        log.info("[start] stage: %s", stage_name)
        t0 = time.time()

        writer = ShardWriter(
            base_dir=self.output_dir,
            entity_type=entity_type,
            partition_keys=partition_keys or [],
            shard_rows=self.config.shard_rows,
        )

        for batch in generator:
            writer.write_batch(batch)
            rss = _check_ram()
            if rss > MAX_RAM_GB:
                log.warning("RAM %.2f GB > threshold", rss)

        stats = writer.close()
        self._file_stats.extend(stats["files"])
        self._row_counts[stage_name] = stats["total_rows"]

        elapsed = time.time() - t0
        log.info(
            "[done] Stage '%s': %d rows, %d shards in %.1fs",
            stage_name, stats["total_rows"], stats["shards"], elapsed,
        )

        self.ckpt.mark_stage_done(stage_name, stats["total_rows"])
        return stats["total_rows"]

    # ── Main run ──────────────────────────────────────────────────────────────

    def run(self) -> Dict[str, Any]:
        """Execute all generation stages in dependency order."""
        os.makedirs(self.output_dir, exist_ok=True)

        if not self.resume:
            # Empirical: ~27 bytes/row (Snappy Parquet, from Profile B). Add 50% margin.
            est_gb = max(0.5, (self.config.cdrs + self.config.transactions) * 27 * 1.5 / 1e9)
            self._check_disk(est_gb=est_gb)

        self.ckpt.initialize(self.config.name, self.config.seed)

        # -- Stage 0: Assign scenarios to population ---------------------------
        log.info("Building population index (%d persons)...", self.config.persons)
        t_pop = time.time()
        
        # Load manifests for Demo World if present
        manifests = None
        manifest_dir = os.path.join(os.path.dirname(__file__), "..", "demo")
        if os.path.exists(manifest_dir) and os.path.exists(os.path.join(manifest_dir, "investigations.json")):
            from .manifest_loader import load_and_validate_manifests
            manifests = load_and_validate_manifests(manifest_dir)
            log.info("Loaded Gemini manifests for Demo World injection.")
            
        population, self.role_resolver = assign_scenarios(self.config, self.seed_bank, manifests)
        log.info("Population index built in %.1fs (%.1f MB)", time.time() - t_pop, len(population) * 120 / 1e6)

        # -- Stage 1: Geography ------------------------------------------------
        self._run_stage(
            "locations", generate_locations(self.config, self.seed_bank),
            "locations",
        )
        self._run_stage(
            "cell_sectors", generate_cell_sectors(self.config, self.seed_bank),
            "cell_sectors",
        )

        # Build runtime indexes
        phone_index = [
            f"__ph_{i:09d}" for i in range(self.config.phone_numbers)
        ]  # placeholder; real UUIDs generated in telecom stage
        cell_index = build_cell_index(self.config, self.seed_bank)

        # -- Stage 2: Entities -------------------------------------------------
        self._run_stage(
            "persons", generate_persons(self.config, population, self.seed_bank),
            "persons",
        )
        self._run_stage(
            "organisations", generate_organisations(self.config, self.seed_bank),
            "organisations",
        )

        # -- Stage 3: Telecom entities -----------------------------------------
        self._run_stage(
            "phones", generate_phones(self.config, self.seed_bank),
            "phones",
        )
        self._run_stage(
            "sims", generate_sims(self.config, self.seed_bank),
            "sims",
        )
        self._run_stage(
            "devices", generate_devices(self.config, self.seed_bank),
            "devices",
        )

        # Build phone UUID index from seeds (fast, no I/O)
        from .seeds import make_uuid
        phone_index = [
            make_uuid("civix-large-phone", self.config.seed, i)
            for i in range(self.config.phone_numbers)
        ]

        # -- Stage 4: CDRs (the heavy stage) -----------------------------------
        self._run_stage(
            "cdrs",
            generate_cdrs(self.config, population, phone_index, cell_index, self.seed_bank),
            "cdrs",
            partition_keys=["year", "month"],
        )

        # -- Stage 5: Financial -------------------------------------------------
        account_index = [
            make_uuid("civix-large-account", self.config.seed, i)
            for i in range(self.config.accounts)
        ]
        self._run_stage(
            "accounts", generate_accounts(self.config, population, self.seed_bank),
            "accounts",
        )
        self._run_stage(
            "transactions",
            generate_transactions(self.config, population, account_index, self.seed_bank),
            "transactions",
            partition_keys=["year", "month"],
        )

        # -- Stage 6: Cases ----------------------------------------------------
        self._run_stage(
            "cases", generate_cases(self.config, population, self.seed_bank),
            "cases",
        )
        self._run_stage(
            "case_entity_roles",
            generate_case_entity_roles(self.config, population, self.seed_bank),
            "case_entity_roles",
        )

        # -- Stage 7: Ground truth labels (SEPARATE directory) -----------------
        gt_dir = os.path.join(self.output_dir, "ground_truth")
        os.makedirs(gt_dir, exist_ok=True)

        gt_writer = ShardWriter(gt_dir, "person_labels", shard_rows=self.config.shard_rows)
        for batch in generate_person_labels(self.config, population):
            gt_writer.write_batch(batch)
        gt_stats = gt_writer.close()
        self._file_stats.extend(gt_stats["files"])
        self._row_counts["person_labels"] = gt_stats["total_rows"]

        split_writer = ShardWriter(gt_dir, "train_val_test_split", shard_rows=self.config.shard_rows)
        for batch in generate_train_val_test_split(self.config, population):
            split_writer.write_batch(batch)
        split_stats = split_writer.close()
        self._file_stats.extend(split_stats["files"])
        self._row_counts["train_val_test_split"] = split_stats["total_rows"]

        self.ckpt.mark_stage_done("ground_truth", gt_stats["total_rows"])

        # -- Stage 7.5: Demo Manifest Constraint Injection ---------------------
        if manifests:
            log.info("Translating Gemini evidence constraints into exact Parquet events...")
            from .translator import translate_evidence
            translate_evidence(manifests, self.role_resolver, self.config.seed, self.output_dir)

        # -- Stage 8: ML Feature aggregation (DuckDB, post-generation) ---------
        log.info("Aggregating ML features via DuckDB...")
        ml_dir = os.path.join(self.output_dir, "ml_features")
        try:
            feat_results = generate_person_behavior_features(
                self.output_dir,
                self.config.name,
                ml_dir,
            )
            for name, res in feat_results.items():
                log.info("  Feature '%s': %s", name, res.get("status", "?"))
        except Exception as e:
            log.warning("Feature aggregation skipped: %s", e)

        # ── Manifest ──────────────────────────────────────────────────────────
        config_dict = dataclasses.asdict(self.config) if hasattr(dataclasses, 'asdict') else {}
        manifest = build_manifest(
            profile_name=self.config.name,
            seed=self.config.seed,
            config_dict={
                "profile": self.config.name,
                "persons": self.config.persons,
                "cdrs": self.config.cdrs,
                "transactions": self.config.transactions,
                "cases": self.config.cases,
                "date_start": self.config.date_start,
                "date_end": self.config.date_end,
            },
            file_stats=self._file_stats,
            row_counts=self._row_counts,
            started_at=self._started_at,
        )
        manifest_path = write_manifest(manifest, self.output_dir)
        log.info("Manifest written: %s", manifest_path)

        elapsed_total = time.time() - self._started_at
        log.info(
            "\n[DONE] Generation complete in %.1fs.\n"
            "   Total rows  : %d\n"
            "   Total shards: %d\n"
            "   Total bytes : %d (%.2f GB)\n"
            "   Output dir  : %s",
            elapsed_total,
            manifest["total_rows"],
            manifest["total_files"],
            manifest["total_bytes"],
            manifest["total_bytes"] / (1 << 30),
            self.output_dir,
        )

        return manifest
