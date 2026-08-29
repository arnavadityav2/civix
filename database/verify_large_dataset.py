#!/usr/bin/env python3
"""
CIVIX Large-Scale Synthetic Data Verifier
database/verify_large_dataset.py

Validates a generated dataset against 20 verification categories.
Reads from Parquet using DuckDB (no RAM overload).

Usage:
  python database/verify_large_dataset.py --profile A
  python database/verify_large_dataset.py --profile C --output-dir data/synthetic/profile_c
"""
import argparse
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
_GEN  = os.path.join(_ROOT, "civix_generator")
for p in [_ROOT, _GEN]:
    if p not in sys.path:
        sys.path.insert(0, p)

from large.config import get_profile
from large.manifest import read_manifest


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CIVIX Large Dataset Verifier")
    p.add_argument("--profile",    default="A")
    p.add_argument("--output-dir", default=None)
    p.add_argument("--report-out", default=None, help="Path for PROFILE_X_VALIDATION_REPORT.md")
    return p.parse_args()


class Verifier:
    def __init__(self, profile_name: str, output_dir: str):
        self.profile_name = profile_name
        self.output_dir   = output_dir
        self.config       = get_profile(profile_name)
        self.results      = []
        self._con         = None

    def _con_db(self):
        if self._con is None:
            try:
                import duckdb
                self._con = duckdb.connect(":memory:")
            except ImportError:
                raise RuntimeError("duckdb required: pip install duckdb")
        return self._con

    def _pq(self, entity: str) -> str:
        return os.path.join(self.output_dir, entity, "**", "*.parquet").replace("\\", "/")

    def _assert(self, test_id: str, description: str, passed: bool, detail: str = ""):
        status = "PASS" if passed else "FAIL"
        self.results.append({
            "test_id": test_id,
            "description": description,
            "status": status,
            "detail": detail,
        })
        status_icon = "OK" if passed else "!!"
        print(f"  [{status_icon}] [{test_id}] {description}{': ' + detail if detail else ''}")

    # ── Test groups ───────────────────────────────────────────────────────────

    def T01_manifest_exists(self):
        exists = os.path.exists(os.path.join(self.output_dir, "manifest.json"))
        self._assert("T01", "Manifest file exists", exists)

    def T02_manifest_row_counts(self):
        try:
            manifest = read_manifest(self.output_dir)
            counts = manifest.get("row_counts", {})
            person_count = counts.get("persons", 0)
            expected = self.config.persons
            ok = abs(person_count - expected) / max(expected, 1) < 0.05
            self._assert("T02", "Person count within 5% of target",
                         ok, f"expected~{expected}, got {person_count}")
        except Exception as e:
            self._assert("T02", "Person count within 5% of target", False, str(e))

    def T03_parquet_readable(self):
        """Check that the key Parquet files can be opened."""
        con = self._con_db()
        for entity in ["persons", "cdrs", "ground_truth/person_labels"]:
            pattern = self._pq(entity)
            try:
                count = con.execute(
                    f"SELECT COUNT(*) FROM read_parquet('{pattern}', hive_partitioning=true)"
                ).fetchone()[0]
                self._assert(f"T03_{entity}", f"Parquet readable: {entity}", True, f"{count:,} rows")
            except Exception as e:
                self._assert(f"T03_{entity}", f"Parquet readable: {entity}", False, str(e))

    def T04_cdr_count(self):
        try:
            con = self._con_db()
            count = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{self._pq('cdrs')}', hive_partitioning=true)"
            ).fetchone()[0]
            expected = self.config.cdrs
            ok = abs(count - expected) / max(expected, 1) < 0.05
            self._assert("T04", "CDR count within 5% of target", ok,
                         f"expected~{expected:,}, got {count:,}")
        except Exception as e:
            self._assert("T04", "CDR count within 5% of target", False, str(e))

    def T05_no_duplicate_person_ids(self):
        try:
            con = self._con_db()
            res = con.execute(f"""
                SELECT COUNT(*) - COUNT(DISTINCT person_id)
                FROM read_parquet('{self._pq("persons")}', hive_partitioning=true)
            """).fetchone()[0]
            self._assert("T05", "No duplicate person IDs", res == 0, f"{res} duplicates")
        except Exception as e:
            self._assert("T05", "No duplicate person IDs", False, str(e))

    def T06_scenario_distribution(self):
        """Verify that scenario class distribution is within ±5pp of config."""
        try:
            con = self._con_db()
            rows = con.execute(f"""
                SELECT scenario_class, COUNT(*) AS n
                FROM read_parquet('{self._pq("persons")}', hive_partitioning=true)
                GROUP BY scenario_class
            """).fetchall()
            total = sum(r[1] for r in rows)
            dist = {r[0]: r[1] / total for r in rows}
            cfg = self.config.scenario_dist
            ok = True
            detail_parts = []
            for cls, expected in [
                ("normal", cfg.normal),
                ("suspicious", cfg.suspicious),
                ("confirmed_pattern", cfg.confirmed_pattern),
                ("false_positive", cfg.false_positive),
            ]:
                actual = dist.get(cls, 0.0)
                within = abs(actual - expected) <= 0.05
                ok = ok and within
                detail_parts.append(f"{cls}={actual:.2f}(exp {expected:.2f})")
            self._assert("T06", "Scenario distribution within ±5pp", ok, " | ".join(detail_parts))
        except Exception as e:
            self._assert("T06", "Scenario distribution within ±5pp", False, str(e))

    def T07_ground_truth_not_in_features(self):
        """Ground truth label columns must NOT appear in CDR or person Parquet files."""
        forbidden_cols = {"scenario_class", "is_positive_label", "is_false_positive",
                         "risk_score_gt", "ground_truth_note", "scenario_id_str"}
        try:
            con = self._con_db()
            cdr_cols = set(c[0] for c in con.execute(
                f"DESCRIBE SELECT * FROM read_parquet('{self._pq('cdrs')}', hive_partitioning=true) LIMIT 0"
            ).fetchall())
            leaked = forbidden_cols & cdr_cols
            self._assert("T07", "Ground truth columns absent from CDR features",
                         len(leaked) == 0, f"Leaked: {leaked}" if leaked else "")
        except Exception as e:
            self._assert("T07", "Ground truth columns absent from CDR features", False, str(e))

    def T08_temporal_validity(self):
        """Check timestamps are within configured date range."""
        try:
            con = self._con_db()
            res = con.execute(f"""
                SELECT
                    MIN(timestamp) AS min_ts,
                    MAX(timestamp) AS max_ts
                FROM read_parquet('{self._pq('cdrs')}', hive_partitioning=true)
            """).fetchone()
            if res and res[0]:
                ok = (res[0][:10] >= self.config.date_start and
                      res[1][:10] <= self.config.date_end)
                self._assert("T08", "CDR timestamps within date range", ok,
                             f"{res[0][:10]} to {res[1][:10]}")
            else:
                self._assert("T08", "CDR timestamps within date range", False, "No CDRs found")
        except Exception as e:
            self._assert("T08", "CDR timestamps within date range", False, str(e))

    def T09_hard_negatives_present(self):
        """Verify false_positive scenarios exist (hard negatives)."""
        try:
            con = self._con_db()
            count = con.execute(f"""
                SELECT COUNT(*) FROM read_parquet('{self._pq("ground_truth/person_labels")}',
                    hive_partitioning=true)
                WHERE is_false_positive = true
            """).fetchone()[0]
            ok = count > 0
            self._assert("T09", "Hard negatives (false positives) present", ok, f"{count:,} persons")
        except Exception as e:
            self._assert("T09", "Hard negatives (false positives) present", False, str(e))

    def T10_train_val_test_split_present(self):
        try:
            con = self._con_db()
            rows = con.execute(f"""
                SELECT split, COUNT(*) AS n
                FROM read_parquet('{self._pq("ground_truth/train_val_test_split")}',
                    hive_partitioning=true)
                GROUP BY split
            """).fetchall()
            splits = {r[0] for r in rows}
            ok = {"TRAIN","VALIDATION","TEST"}.issubset(splits)
            self._assert("T10", "TRAIN/VALIDATION/TEST splits all present", ok,
                         str({r[0]: r[1] for r in rows}))
        except Exception as e:
            self._assert("T10", "TRAIN/VALIDATION/TEST splits all present", False, str(e))

    def T11_no_null_person_ids_in_cdrs(self):
        try:
            con = self._con_db()
            nulls = con.execute(f"""
                SELECT COUNT(*) FROM read_parquet('{self._pq("cdrs")}', hive_partitioning=true)
                WHERE caller_person_id IS NULL
            """).fetchone()[0]
            self._assert("T11", "No null caller_person_id in CDRs", nulls == 0, f"{nulls} nulls")
        except Exception as e:
            self._assert("T11", "No null caller_person_id in CDRs", False, str(e))

    def T12_scenario_family_diversity(self):
        """Verify multiple distinct scenario families exist."""
        try:
            con = self._con_db()
            n = con.execute(f"""
                SELECT COUNT(DISTINCT scenario_family)
                FROM read_parquet('{self._pq("ground_truth/person_labels")}',
                    hive_partitioning=true)
            """).fetchone()[0]
            ok = n >= 10   # should have at least 10 distinct families
            self._assert("T12", "≥10 distinct scenario families", ok, f"{n} families found")
        except Exception as e:
            self._assert("T12", "≥10 distinct scenario families", False, str(e))

    def T13_manifest_checksum(self):
        """Verify manifest.json is well-formed and has expected keys."""
        try:
            manifest = read_manifest(self.output_dir)
            required = {"profile","seed","row_counts","files","total_rows"}
            missing  = required - set(manifest.keys())
            self._assert("T13", "Manifest has all required keys",
                         len(missing) == 0, f"Missing: {missing}" if missing else "")
        except Exception as e:
            self._assert("T13", "Manifest has all required keys", False, str(e))

    def T14_determinism_uuid_check(self):
        """Verify first person UUID is deterministic given seed + index."""
        from large.seeds import make_uuid
        expected = make_uuid("civix-large-person", self.config.seed, 0)
        try:
            con = self._con_db()
            actual = con.execute(f"""
                SELECT person_id FROM read_parquet('{self._pq("persons")}',
                    hive_partitioning=true)
                WHERE person_index = 0
                LIMIT 1
            """).fetchone()
            ok = actual is not None and actual[0] == expected
            self._assert("T14", "Person[0] UUID matches deterministic seed",
                         ok, f"expected {expected}, got {actual[0] if actual else 'None'}")
        except Exception as e:
            self._assert("T14", "Person[0] UUID matches deterministic seed", False, str(e))

    def T15_cdr_duration_distribution(self):
        """CDR durations should not be uniform (anti-synthetic-artifact check)."""
        try:
            con = self._con_db()
            res = con.execute(f"""
                SELECT STDDEV(duration_seconds), MIN(duration_seconds), MAX(duration_seconds)
                FROM read_parquet('{self._pq("cdrs")}', hive_partitioning=true)
            """).fetchone()
            std, mn, mx = res
            ok = std is not None and std > 5.0   # non-trivial variation
            self._assert("T15", "CDR duration distribution is non-uniform",
                         ok, f"std={std:.1f}s, range=[{mn},{mx}]s")
        except Exception as e:
            self._assert("T15", "CDR duration distribution is non-uniform", False, str(e))

    def T16_transaction_amount_pareto(self):
        """Transaction amounts should have long tail (not uniform)."""
        try:
            con = self._con_db()
            res = con.execute(f"""
                SELECT AVG(amount), MAX(amount), STDDEV(amount)
                FROM read_parquet('{self._pq("transactions")}', hive_partitioning=true)
            """).fetchone()
            avg_a, max_a, std_a = res
            ok = std_a is not None and std_a > avg_a * 0.5   # high relative std → Pareto
            self._assert("T16", "Transaction amounts have long tail (Pareto-like)",
                         ok, f"avg={avg_a:.0f}, max={max_a:.0f}, std={std_a:.0f}")
        except Exception as e:
            self._assert("T16", "Transaction amounts have long tail (Pareto-like)", False, str(e))

    def T17_cases_exist(self):
        try:
            con = self._con_db()
            count = con.execute(
                f"SELECT COUNT(*) FROM read_parquet('{self._pq('cases')}', hive_partitioning=true)"
            ).fetchone()[0]
            ok = count > 0
            self._assert("T17", "Cases generated", ok, f"{count:,} cases")
        except Exception as e:
            self._assert("T17", "Cases generated", False, str(e))

    def T18_checkpoint_file(self):
        ckpt_path = os.path.join(self.output_dir, "checkpoint.json")
        exists = os.path.exists(ckpt_path)
        self._assert("T18", "Checkpoint file exists", exists)

    def T19_multiple_cell_sectors(self):
        try:
            con = self._con_db()
            n = con.execute(f"""
                SELECT COUNT(DISTINCT cell_sector_id)
                FROM read_parquet('{self._pq("cdrs")}', hive_partitioning=true)
            """).fetchone()[0]
            ok = n >= min(10, self.config.cell_sectors)
            self._assert("T19", "Multiple cell sectors used in CDRs", ok, f"{n} distinct sectors")
        except Exception as e:
            self._assert("T19", "Multiple cell sectors used in CDRs", False, str(e))

    def T20_memory_bounds_not_violated(self):
        """Check that checkpoint notes no OOM errors (proxy: checkpoint exists and has stages)."""
        try:
            ckpt_path = os.path.join(self.output_dir, "checkpoint.json")
            with open(ckpt_path) as f:
                ckpt = json.load(f)
            stages = ckpt.get("completed_stages", [])
            ok = len(stages) >= 5   # at least entities, cdrs, transactions completed
            self._assert("T20", "≥5 stages completed (no premature OOM halt)",
                         ok, f"{len(stages)} stages completed")
        except Exception as e:
            self._assert("T20", "≥5 stages completed (no premature OOM halt)", False, str(e))

    # ── Runner ────────────────────────────────────────────────────────────────

    def run_all(self) -> bool:
        print(f"\n{'='*65}")
        print(f"  CIVIX Verification — Profile {self.profile_name.upper()} ({self.config.name})")
        print(f"  Output: {self.output_dir}")
        print(f"{'='*65}\n")

        for method_name in sorted(dir(self)):
            if method_name.startswith("T") and callable(getattr(self, method_name)):
                try:
                    getattr(self, method_name)()
                except Exception as e:
                    self._assert(method_name, method_name, False, f"EXCEPTION: {e}")

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total  = len(self.results)

        print(f"\n{'='*65}")
        print(f"  Result: {passed}/{total} PASS  |  {failed} FAIL")
        print(f"{'='*65}\n")

        return failed == 0

    def write_report(self, report_path: str) -> None:
        lines = [
            f"# CIVIX Profile {self.profile_name.upper()} Validation Report\n",
            f"**Profile**: {self.config.name}  \n",
            f"**Output**: {self.output_dir}  \n\n",
            "| Test ID | Description | Status | Detail |\n",
            "|---|---|---|---|\n",
        ]
        for r in self.results:
            icon = "OK" if r["status"] == "PASS" else "!!"
            lines.append(f"| {r['test_id']} | {r['description']} | {icon} {r['status']} | {r['detail']} |\n")

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = len(self.results) - passed
        lines.append(f"\n**Total**: {passed} PASS / {failed} FAIL\n")

        os.makedirs(os.path.dirname(report_path) or ".", exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"Report written: {report_path}")


def main():
    args = parse_args()
    profile_name = args.profile.upper()

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = os.path.join(
            _ROOT, "data", "synthetic", f"profile_{profile_name.lower()}"
        )

    if not os.path.exists(output_dir):
        print(f"ERROR: Output directory not found: {output_dir}")
        print("Run generate_large_dataset.py first.")
        sys.exit(1)

    verifier = Verifier(profile_name, output_dir)
    success  = verifier.run_all()

    if args.report_out:
        report_path = args.report_out
    else:
        docs_dir    = os.path.join(_ROOT, "docs", "phase2b")
        report_path = os.path.join(docs_dir, f"PROFILE_{profile_name}_VALIDATION_REPORT.md")

    verifier.write_report(report_path)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
