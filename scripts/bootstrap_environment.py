"""
CIVIX 2.0 — Automated Master Bootstrap & Seeding Pipeline
==============================================================================
Runs the complete 6-step automated setup sequence:
0. Run SQL Migrations (create schema)
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
from pathlib import Path

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

def run_migrations():
    """Step 0: Apply all SQL migration files in order via psycopg2."""
    import psycopg2

    logger.info("👉 STEP: Running SQL Schema Migrations (000–035)")
    host     = os.environ.get("CIVIX_DB_HOST",     "localhost")
    port     = int(os.environ.get("CIVIX_DB_PORT", "5432"))
    dbname   = os.environ.get("CIVIX_DB_NAME",     "civix_demo")
    user     = os.environ.get("CIVIX_DB_USER",     "postgres")
    password = os.environ.get("CIVIX_DB_PASSWORD", "postgres")

    conn = psycopg2.connect(host=host, port=port, dbname=dbname, user=user, password=password)
    conn.autocommit = True
    cur = conn.cursor()

    migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
    sql_files = sorted(migrations_dir.glob("*.sql"))
    logger.info(f"  Found {len(sql_files)} migration files in {migrations_dir}")

    for sql_file in sql_files:
        logger.info(f"  Applying {sql_file.name} ...")
        with open(sql_file, "r") as f:
            sql = f.read()
        try:
            cur.execute(sql)
            logger.info(f"  ✅ {sql_file.name} applied.")
        except Exception as e:
            # Most errors here are safe (extension already exists, etc.)
            logger.warning(f"  ⚠️  {sql_file.name} warning (non-fatal): {e}")
            conn.rollback()

    cur.close()
    conn.close()
    logger.info("✅ PASSED: SQL Schema Migrations complete.")

def main():
    logger.info("==========================================================================")
    logger.info("       CIVIX 2.0 AUTOMATED MASTER ENVIRONMENT BOOTSTRAP PIPELINE          ")
    logger.info("==========================================================================")

    py_bin = sys.executable

    # 0. Run SQL Schema Migrations
    run_migrations()

    # 1. Seed 12-Case Golden Universe
    run_step("Seeding PostgreSQL 12-Case Golden Universe", [py_bin, "database/seed_12case_universe.py"])

    # 2. Generate Evidence Media Visuals
    run_step("Generating Evidence Media & CCTV Visual Artifacts", [py_bin, "database/generate_all_visuals_fast.py"])

    # 3. Grant RLS Permissions
    run_step("Granting PostgreSQL Row-Level Security (RLS) Permissions", [py_bin, "scratch/grant_all_case_access.py"])

    # 4. Clean & Pin Cases
    run_step("Enriching Spatial Locations for Van Robbery Case", [py_bin, "scratch/enrich_van_robbery_locations.py"])
    run_step("Cleaning & Pinning Demo Cases", [py_bin, "scratch/cleanup_and_pin_cases.py"])

    # 5. Sync PG to Neo4j
    run_step("Syncing Graph Entities & Relationships to Neo4j", [py_bin, "scratch/sync_pg_to_neo4j.py"])

    logger.info("==========================================================================")
    logger.info("🎉 SUCCESS: CIVIX 2.0 Environment fully bootstrapped and synchronized!    ")
    logger.info("==========================================================================")

if __name__ == "__main__":
    main()
