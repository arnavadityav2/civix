"""
CIVIX Synthetic World V2 — Command Line Interface
civix_generator/v2/cli.py

Usage:
    python -m civix_generator.v2.cli --profile DEV --out-dir D:/civix_data/synthetic/profile_v2_dev
    python -m civix_generator.v2.cli --profile V2A
    python -m civix_generator.v2.cli --profile V2A --validate-only
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="CIVIX Synthetic World V2 Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Profiles:
  DEV   5,000 persons   (smoke test, < 3 min)
  INT   50,000 persons  (integration test, ~15 min)
  V2A   250,000 persons SEED-A (primary training set, ~90 min)
  V2B   50,000 persons  SEED-B (cross-seed eval 1)
  V2C   50,000 persons  SEED-C (cross-seed eval 2)
        """,
    )
    parser.add_argument("--profile",       default="DEV",  help="Profile name (DEV/INT/V2A/V2B/V2C)")
    parser.add_argument("--out-dir",       default=None,   help="Output directory (default: D:/civix_data/...)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip stages whose output already exists")
    parser.add_argument("--validate-only", action="store_true", help="Run validation gates on existing dataset only")
    parser.add_argument("--no-strict",     action="store_true", help="Don't raise on gate failure (report all)")

    args = parser.parse_args()

    if args.validate_only:
        from civix_generator.v2.validation.gates import run_all_gates
        out_dir = args.out_dir or f"D:/civix_data/synthetic/profile_v2_{args.profile.lower()}"
        print(f"\nRunning validation gates on: {out_dir}")
        results = run_all_gates(out_dir, strict=not args.no_strict)
        failed = [r for r in results if not r.passed]
        sys.exit(1 if failed else 0)
    else:
        from civix_generator.v2.runner import run_v2
        out_path = run_v2(
            profile=args.profile,
            out_dir=args.out_dir,
            skip_existing=args.skip_existing,
        )

        # Auto-run gates after generation
        print("\nRunning validation gates...")
        from civix_generator.v2.validation.gates import run_all_gates
        results = run_all_gates(str(out_path), strict=not args.no_strict)
        failed = [r for r in results if not r.passed and r.gate_id <= 11]

        sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
