"""
CIVIX 2.0 — Automated Master Bootstrap & Seeding Pipeline
==============================================================================
Runs the complete 5-step automated setup sequence:
1. Seed PostgreSQL 12-Case Golden Universe
2. Generate Evidence Media & CCTV Visual Artifacts
3. Grant RLS Permissions for Investigator Vikram S.
4. Clean up & Pin Demo Cases
5. Sync PostgreSQL Graph Entities to Neo4j
==============================================================================
"""

import sys
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("civix.bootstrap")

def run_step(description: str, command: list):
    logger.info(f"👉 STEP: {description}")
    try:
        res = subprocess.run(command, check=True, text=True, capture_output=True)
        if res.stdout:
            print(res.stdout)
        logger.info(f"✅ PASSED: {description}")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ FAILED: {description}")
        logger.error(e.stderr)
        raise e

def main():
    logger.info("==========================================================================")
    logger.info("       CIVIX 2.0 AUTOMATED MASTER ENVIRONMENT BOOTSTRAP PIPELINE          ")
    logger.info("==========================================================================")

    py_bin = sys.executable

    # 1. Seed 12-Case Golden Universe
    run_step("Seeding PostgreSQL 12-Case Golden Universe", [py_bin, "database/seed_12case_universe.py"])

    # 2. Generate Evidence Media Visuals
    run_step("Generating Evidence Media & CCTV Visual Artifacts", [py_bin, "database/generate_all_visuals_fast.py"])

    # 3. Grant RLS Permissions
    run_step("Granting PostgreSQL Row-Level Security (RLS) Permissions", [py_bin, "scratch/grant_all_case_access.py"])

    # 4. Clean & Pin Cases
    run_step("Cleaning & Pinning Demo Cases", [py_bin, "scratch/cleanup_and_pin_cases.py"])

    # 5. Sync PG to Neo4j
    run_step("Syncing Graph Entities & Relationships to Neo4j", [py_bin, "scratch/sync_pg_to_neo4j.py"])

    logger.info("==========================================================================")
    logger.info("🎉 SUCCESS: CIVIX 2.0 Environment fully bootstrapped and synchronized!    ")
    logger.info("==========================================================================")

if __name__ == "__main__":
    main()
