"""
CIVIX Synthetic World V2: Top-Level Orchestration Runner
civix_generator/v2/runner.py

Executes all generation stages in order:
    Stage 1:  Population + latent trait assignment
    Stage 2:  Adversarial modifications (hard negatives, low-visibility criminals)
    Stage 3:  Community structure generation
    Stage 4:  Temporal lifecycle assignment
    Stage 5:  Geography (locations, cell sectors, home/work assignment)
    Stage 6:  Devices + SIMs + Phones
    Stage 7:  Identity entities (observable person fields)
    Stage 8:  Financial accounts
    Stage 9:  CDR generation (community-aware, reciprocal, temporal)
    Stage 10: Transaction generation
    Stage 11: Ground truth labels
    Stage 12: Train/val/test split
    Stage 13: Community catalog output
    Stage 14: Manifest + checksums

Usage:
    from civix_generator.v2.runner import run_v2
    run_v2(profile="DEV", out_dir="D:/civix_data/synthetic/profile_v2_dev")
"""
from __future__ import annotations
import json
import os
import time
from pathlib import Path
from typing import Optional

from .config import get_v2_profile, V2ProfileConfig
from .seeds import V2SeedBank, make_uuid
from .population import assign_population
from .adversarial_engine import apply_adversarial_modifications
from .community import build_communities
from .temporal_engine import assign_lifecycles, get_lifecycle_stats
from .geography import (
    generate_locations_v2, generate_cell_sectors_v2,
    build_cell_index_v2, assign_home_work_locations,
)
from .devices import (
    generate_devices_v2, generate_sims_v2,
    generate_phones_v2, build_phone_index_v2,
)
from .identity import generate_persons_v2
from .financial import generate_accounts_v2, generate_transactions_v2
from .communication import generate_cdrs_v2
from .ground_truth import generate_person_labels, generate_train_val_test_split
from .streaming_writer import ShardWriter, write_manifest
from .parquet_writer import (
    PERSON_SCHEMA, CDR_SCHEMA, TRANSACTION_SCHEMA, ACCOUNT_SCHEMA,
    DEVICE_SCHEMA, SIM_SCHEMA, PHONE_SCHEMA, LOCATION_SCHEMA,
    CELL_SCHEMA, LABEL_SCHEMA, SPLIT_SCHEMA, COMMUNITY_SCHEMA,
)
import pyarrow as pa


def run_v2(
    profile: str = "DEV",
    out_dir: Optional[str] = None,
    skip_existing: bool = False,
) -> Path:
    """
    Run the full V2 generation pipeline.

    Args:
        profile:      V2 profile name (DEV, INT, V2A, V2B, V2C)
        out_dir:      Output directory. Default: D:\\civix_data\\synthetic\\profile_v2_{profile.lower()}
        skip_existing: If True, skip stages whose output dirs already exist.

    Returns:
        Path to the output directory.
    """
    config = get_v2_profile(profile)

    if out_dir is None:
        out_dir = f"D:/civix_data/synthetic/profile_v2_{profile.lower()}"

    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  CIVIX Synthetic World V2 Generator")
    print(f"  Profile: {profile}  ({config.persons:,} persons)")
    print(f"  Output:  {out_path}")
    print(f"  Seed:    {config.seed}")
    print(f"{'='*70}\n")

    seed_bank    = V2SeedBank(config.seed)
    artifact_summary: dict = {}
    t0 = time.time()

    # â”€â”€ Stage 1: Population + Latent Traits â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("1", "Population + Latent Traits")
    population = assign_population(config, seed_bank)
    print(f"     â†’ {len(population):,} persons assigned with 14 latent traits")

    # â”€â”€ Stage 2: Adversarial Modifications â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("2", "Adversarial Modifications (Hard Negatives + Low-Visibility Criminals)")
    apply_adversarial_modifications(population, config, seed_bank)
    n_hn  = sum(1 for p in population if p.get("_hard_negative"))
    n_lv  = sum(1 for p in population if p.get("_low_visibility"))
    print(f"     â†’ {n_hn:,} hard negatives, {n_lv:,} low-visibility criminals injected")

    # â”€â”€ Stage 3: Community Structure â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("3", "Community Structure (Family / Workplace / Social / Criminal)")
    contact_pools, community_catalog = build_communities(population, config, seed_bank)
    n_criminal_comms = sum(1 for m in community_catalog.values() if m["is_criminal"])
    print(f"     â†’ {len(community_catalog):,} communities "
          f"({n_criminal_comms} criminal, {len(community_catalog) - n_criminal_comms} legitimate)")

    # â”€â”€ Stage 4: Temporal Lifecycle â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("4", "Temporal Lifecycle Assignment")
    lifecycles = assign_lifecycles(population, config, seed_bank)
    lc_stats   = get_lifecycle_stats(lifecycles)
    print(f"     â†’ Phase distribution: {lc_stats['phase_distribution']}")

    # â”€â”€ Stage 5: Geography â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("5", "Geography (Locations + Cell Sectors + Home/Work Assignment)")
    assign_home_work_locations(population, config, seed_bank)
    cell_index = build_cell_index_v2(config)

    loc_dir = out_path / "locations"
    if not _skip_check(loc_dir, skip_existing):
        with ShardWriter(loc_dir, LOCATION_SCHEMA, config.shard_rows) as w:
            for batch in generate_locations_v2(config, seed_bank):
                w.write(batch)
        artifact_summary["locations"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['locations']['rows']:,} locations written")

    cell_dir = out_path / "cell_sectors"
    if not _skip_check(cell_dir, skip_existing):
        with ShardWriter(cell_dir, CELL_SCHEMA, config.shard_rows) as w:
            for batch in generate_cell_sectors_v2(config, seed_bank):
                w.write(batch)
        artifact_summary["cell_sectors"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['cell_sectors']['rows']:,} cell sectors written")

    # â”€â”€ Stage 6: Devices + SIMs + Phones â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("6", "Devices + SIMs + Phones")
    phone_index = build_phone_index_v2(config)

    dev_dir = out_path / "devices"
    if not _skip_check(dev_dir, skip_existing):
        with ShardWriter(dev_dir, DEVICE_SCHEMA, config.shard_rows) as w:
            for batch in generate_devices_v2(config, population, seed_bank):
                w.write(batch)
        artifact_summary["devices"] = {"rows": w.total_rows}

    sim_dir = out_path / "sims"
    if not _skip_check(sim_dir, skip_existing):
        with ShardWriter(sim_dir, SIM_SCHEMA, config.shard_rows) as w:
            for batch in generate_sims_v2(config, population, seed_bank):
                w.write(batch)
        artifact_summary["sims"] = {"rows": w.total_rows}

    ph_dir = out_path / "phones"
    if not _skip_check(ph_dir, skip_existing):
        with ShardWriter(ph_dir, PHONE_SCHEMA, config.shard_rows) as w:
            for batch in generate_phones_v2(config, population, seed_bank):
                w.write(batch)
        artifact_summary["phones"] = {"rows": w.total_rows}

    print(f"     â†’ {config.devices:,} devices, {config.sims:,} SIMs, {config.phone_numbers:,} phones")

    # â”€â”€ Stage 7: Identity Entities â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("7", "Person Identity Entities")
    pers_dir = out_path / "persons"
    if not _skip_check(pers_dir, skip_existing):
        with ShardWriter(pers_dir, PERSON_SCHEMA, config.shard_rows) as w:
            for batch in generate_persons_v2(config, population, seed_bank):
                w.write(batch)
        artifact_summary["persons"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['persons']['rows']:,} persons written")

    # â”€â”€ Stage 8: Financial Accounts â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("8", "Financial Accounts")
    acct_dir = out_path / "accounts"
    account_index: list[str] = []
    if not _skip_check(acct_dir, skip_existing):
        with ShardWriter(acct_dir, ACCOUNT_SCHEMA, config.shard_rows) as w:
            for batch in generate_accounts_v2(config, population, seed_bank):
                account_index.extend([r["account_id"] for r in batch])
                w.write(batch)
        artifact_summary["accounts"] = {"rows": w.total_rows}
    else:
        # Rebuild account_index from seed for reproducibility
        from .seeds import make_uuid as _mu
        account_index = [_mu("civix-v2-account", config.seed, i) for i in range(config.accounts)]
    print(f"     â†’ {len(account_index):,} accounts")

    # â”€â”€ Stage 9: CDR Generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("9", "CDR Generation (V2: Community-Aware, Reciprocal, Temporal)")
    cdr_dir = out_path / "cdrs"
    if not _skip_check(cdr_dir, skip_existing):
        with ShardWriter(cdr_dir, CDR_SCHEMA, config.shard_rows) as w:
            for batch in generate_cdrs_v2(
                config, population, contact_pools, phone_index, cell_index, lifecycles, seed_bank
            ):
                w.write(batch)
        artifact_summary["cdrs"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['cdrs']['rows']:,} CDRs written")

    # â”€â”€ Stage 10: Transaction Generation â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("10", "Transaction Generation (V2: Income-Band Aware)")
    txn_dir = out_path / "transactions"
    if not _skip_check(txn_dir, skip_existing):
        with ShardWriter(txn_dir, TRANSACTION_SCHEMA, config.shard_rows) as w:
            for batch in generate_transactions_v2(config, population, account_index, seed_bank):
                w.write(batch)
        artifact_summary["transactions"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['transactions']['rows']:,} transactions written")

    # â”€â”€ Stage 11: Ground Truth Labels â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("11", "Ground Truth Labels (STRICTLY SEPARATED)")
    gt_dir = out_path / "ground_truth" / "person_labels"
    if not _skip_check(gt_dir, skip_existing):
        with ShardWriter(gt_dir, LABEL_SCHEMA, config.shard_rows) as w:
            for batch in generate_person_labels(config, population, community_catalog, seed_bank):
                w.write(batch)
        artifact_summary["ground_truth_labels"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['ground_truth_labels']['rows']:,} label records written")

    # â”€â”€ Stage 12: Train/Val/Test Split â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("12", "Train / Validation / Test Split")
    split_dir = out_path / "ground_truth" / "train_val_test_split"
    if not _skip_check(split_dir, skip_existing):
        with ShardWriter(split_dir, SPLIT_SCHEMA, config.shard_rows) as w:
            for batch in generate_train_val_test_split(config, population):
                w.write(batch)
        artifact_summary["splits"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['splits']['rows']:,} split records written")

    # â”€â”€ Stage 13: Community Catalog â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("13", "Community Catalog")
    comm_dir = out_path / "communities"
    if not _skip_check(comm_dir, skip_existing):
        comm_records = [
            {
                "community_id": cid,
                "type":         meta["type"],
                "size":         meta["size"],
                "region":       meta["region"],
                "is_criminal":  meta["is_criminal"],
            }
            for cid, meta in community_catalog.items()
        ]
        with ShardWriter(comm_dir, COMMUNITY_SCHEMA, config.shard_rows) as w:
            w.write(comm_records)
        artifact_summary["communities"] = {"rows": w.total_rows}
        print(f"     â†’ {artifact_summary['communities']['rows']:,} community records written")

    # â”€â”€ Stage 14: Manifest + Checksums â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
    _stage("14", "Manifest + Checksums")
    gen_config = {
        "profile":       profile,
        "generator":     "civix-v2-2.0.0",
        "seed":          config.seed,
        "persons":       config.persons,
        "date_start":    config.date_start,
        "date_end":      config.date_end,
        "target_cdrs":   config.target_cdrs,
        "target_txns":   config.target_transactions,
        "scenario_dist": {
            "normal":            config.scenario_dist.normal,
            "suspicious":        config.scenario_dist.suspicious,
            "confirmed_pattern": config.scenario_dist.confirmed_pattern,
            "false_positive":    config.scenario_dist.false_positive,
        },
    }
    write_manifest(out_path, gen_config, artifact_summary)

    elapsed = time.time() - t0
    print(f"\n{'='*70}")
    print(f"  V2 Generation COMPLETE â€” {elapsed:.1f}s")
    print(f"  Output: {out_path}")
    print(f"{'='*70}\n")

    return out_path


def _stage(num: str, name: str) -> None:
    print(f"\n  Stage {num}: {name}")


def _skip_check(path: Path, skip: bool) -> bool:
    exists = path.exists() and any(path.rglob("*.parquet"))
    if exists and skip:
        print(f"     â†’ SKIPPING (output already exists): {path}")
    return exists and skip
