#!/usr/bin/env python3
"""
CIVIX Large-Scale Synthetic Data Generator
database/generate_large_dataset.py

Usage:
  python database/generate_large_dataset.py --profile A
  python database/generate_large_dataset.py --profile C --seed 20260829
  python database/generate_large_dataset.py --profile C --resume
  python database/generate_large_dataset.py --profile C --smoke 0.01  # 1% test
  python database/generate_large_dataset.py --profile D --allow-stress  # explicit opt-in

The script adds the civix_generator/ directory to the path automatically.
"""
import argparse
import os
import sys

# ── Path setup ────────────────────────────────────────────────────────────────
_HERE  = os.path.dirname(os.path.abspath(__file__))
_ROOT  = os.path.dirname(_HERE)
_GEN   = os.path.join(_ROOT, "civix_generator")
for p in [_ROOT, _GEN]:
    if p not in sys.path:
        sys.path.insert(0, p)

from large.config import get_profile
from large.engine import LargeScaleEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CIVIX Large-Scale Synthetic Data Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Profiles:
  A  — Development (1K persons, 250K CDRs)
  B  — Validation  (10K persons, 2.5M CDRs)
  C  — Training    (250K persons, 75M CDRs)   ← PRIMARY DELIVERABLE
  D  — Stress      (5M persons, 1.5B CDRs)    ← requires --allow-stress
        """,
    )
    parser.add_argument("--profile",      default="A",  help="Dataset profile: A|B|C|D")
    parser.add_argument("--seed",         type=int,     help="Override master seed (default: profile seed)")
    parser.add_argument("--output",       default=None, help="Output directory (default: data/synthetic/profile_<X>)")
    parser.add_argument("--resume",       action="store_true", help="Resume from checkpoint")
    parser.add_argument("--overwrite",    action="store_true", help="Overwrite existing output")
    parser.add_argument("--smoke",        type=float, default=1.0,
                        help="Fraction of profile to generate (e.g. 0.01 for 1%% smoke test)")
    parser.add_argument("--geography",    default=None, help="Override geography: ajmer|multi_region")
    parser.add_argument("--allow-stress", action="store_true",
                        help="Required to run Profile D (stress test)")
    parser.add_argument("--verbose",      action="store_true", help="Debug logging")
    parser.add_argument("--dry-run",      action="store_true", help="Show config without generating")
    return parser.parse_args()


def main():
    args = parse_args()

    # ── Profile safety guard ──────────────────────────────────────────────────
    if args.profile.upper() == "D" and not args.allow_stress:
        print(
            "ERROR: Profile D (Stress) requires --allow-stress flag.\n"
            "This profile generates 1.5 BILLION CDRs and must only run\n"
            "on a machine with adequate resources.\n"
            "Add --allow-stress to confirm you intend to run it."
        )
        sys.exit(1)

    # ── Load profile config ───────────────────────────────────────────────────
    config = get_profile(args.profile)

    if args.seed:
        config.seed = args.seed
    if args.geography:
        config.geography = args.geography

    # ── Determine output directory ────────────────────────────────────────────
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.join(
            _ROOT, "data", "synthetic", f"profile_{args.profile.lower()}"
        )

    # ── Dry run ───────────────────────────────────────────────────────────────
    if args.dry_run:
        print(f"\n{'='*60}")
        print(f"  CIVIX Profile {args.profile.upper()}: {config.name}")
        print(f"{'='*60}")
        print(f"  Persons:      {config.persons:>12,}")
        print(f"  CDRs:         {config.cdrs:>12,}")
        print(f"  Transactions: {config.transactions:>12,}")
        print(f"  Cases:        {config.cases:>12,}")
        print(f"  Devices:      {config.devices:>12,}")
        print(f"  SIMs:         {config.sims:>12,}")
        print(f"  Accounts:     {config.accounts:>12,}")
        print(f"  Date range:   {config.date_start} to {config.date_end}")
        print(f"  Seed:         {config.seed}")
        print(f"  Smoke:        {args.smoke*100:.1f}%")
        print(f"  Geography:    {config.geography}")
        print(f"  Output:       {output_dir}")
        print(f"  Shard rows:   {config.shard_rows:,}")
        print(f"  Batch size:   {config.batch_size:,}")
        print(f"\n  Scenario distribution:")
        d = config.scenario_dist
        print(f"    normal:            {d.normal*100:.0f}%")
        print(f"    suspicious:        {d.suspicious*100:.0f}%")
        print(f"    confirmed_pattern: {d.confirmed_pattern*100:.0f}%")
        print(f"    false_positive:    {d.false_positive*100:.0f}%")
        print("\n  [DRY RUN -- no data generated]\n")
        sys.exit(0)

    # -- Pre-flight check ------------------------------------------------------
    if os.path.exists(output_dir) and not args.resume and not args.overwrite:
        print(
            f"ERROR: Output directory already exists: {output_dir}\n"
            f"Use --resume to continue, or --overwrite to start fresh."
        )
        sys.exit(1)

    if args.overwrite and os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
        print(f"Removed existing output: {output_dir}")

    # -- Run engine ------------------------------------------------------------
    print(f"\n  CIVIX Profile {args.profile.upper()} ({config.name})")
    print(f"      {config.persons:,} persons, {config.cdrs:,} CDRs")
    print(f"      Output: {output_dir}\n")

    engine = LargeScaleEngine(
        config=config,
        output_dir=output_dir,
        overwrite=args.overwrite,
        resume=args.resume,
        verbose=args.verbose,
        smoke_fraction=args.smoke,
    )

    manifest = engine.run()

    print(f"\nDone. {manifest['total_rows']:,} total rows, "
          f"{manifest['total_bytes']/(1<<20):.1f} MB, "
          f"{manifest['generation_duration_seconds']}s")


if __name__ == "__main__":
    main()
