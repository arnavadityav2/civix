"""
CIVIX — Backfill: case_entity_role → Neo4j HAS_ROLE projection

Reconciles all existing active case_entity_role rows in PostgreSQL with Neo4j.
Idempotent: safe to run multiple times. Uses MERGE on role_id.

Run once after applying migration 024 to fix pre-existing cases.

Usage:
    python scratch/backfill_case_entity_roles.py

Requires:
    CIVIX_DATABASE_URL_SYNC  — PostgreSQL sync DSN (psycopg)
    NEO4J_URI                — bolt://localhost:7687
    NEO4J_USER               — neo4j
    NEO4J_PASSWORD           — (your password)
"""

import os
import sys
import logging
import psycopg
from neo4j import GraphDatabase
from neo4j.exceptions import TransientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

PG_DSN = os.getenv(
    "CIVIX_DATABASE_URL_SYNC",
    "postgresql://civix_cdc_worker:cdc_worker_pass_123@localhost:5433/civix_test"
)
NEO4J_URI  = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "password")

# Idempotent MERGE: matches on role_id so re-runs create no duplicates.
# Only sets properties when the incoming seq_no is higher — but for a
# backfill we do not have a seq_no, so we use 0 to allow the live CDC
# pipeline to overwrite with the real seq_no if it processes a newer event.
CYPHER_UPSERT = """
MATCH (c:Case {case_id: $case_id})
MATCH (e {entity_id: $entity_id})
MERGE (c)-[r:HAS_ROLE {role_id: $role_id}]->(e)
SET r.role       = $role,
    r.role_basis = $role_basis,
    r.last_seq_no = CASE WHEN r.last_seq_no IS NULL THEN -1 ELSE r.last_seq_no END
RETURN true AS ok
"""


def fetch_active_roles(conn) -> list[dict]:
    """Fetch all currently active (tx_end IS NULL) case_entity_role rows."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT
                cer.role_id::text,
                cer.case_id::text,
                cer.entity_id::text,
                cer.role::text,
                cer.role_basis
            FROM civix.case_entity_role cer
            WHERE cer.tx_end IS NULL
            ORDER BY cer.tx_start ASC
        """)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def project_role(session, row: dict) -> bool:
    """Project a single role row to Neo4j. Returns True on success."""
    try:
        record = session.run(
            CYPHER_UPSERT,
            role_id   = row["role_id"],
            case_id   = row["case_id"],
            entity_id = row["entity_id"],
            role      = row["role"],
            role_basis= row["role_basis"],
        ).single()
        return record is not None
    except TransientError as e:
        logger.warning(f"  TransientError for role {row['role_id']}: {e}")
        return False
    except Exception as e:
        logger.error(f"  Unexpected error for role {row['role_id']}: {type(e).__name__} — {e}")
        return False


def main():
    logger.info("=== CIVIX case_entity_role Backfill ===")

    with psycopg.connect(PG_DSN) as conn:
        rows = fetch_active_roles(conn)

    logger.info(f"Found {len(rows)} active case_entity_role rows to project.")
    if not rows:
        logger.info("Nothing to backfill. Exiting.")
        return

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    success = 0
    failed  = 0

    with driver.session() as session:
        for i, row in enumerate(rows, 1):
            ok = project_role(session, row)
            if ok:
                success += 1
                logger.debug(f"  [{i}/{len(rows)}] OK  role_id={row['role_id']} role={row['role']}")
            else:
                failed += 1
                logger.warning(
                    f"  [{i}/{len(rows)}] FAIL role_id={row['role_id']} "
                    f"case={row['case_id']} entity={row['entity_id']} — "
                    f"Case or Entity node may not yet be in Neo4j. "
                    f"Run the CDC worker first to project entity nodes, then re-run this backfill."
                )

    driver.close()
    logger.info(f"=== Backfill complete: {success} projected, {failed} failed ===")

    if failed > 0:
        logger.warning(
            "Some rows could not be projected. This is expected if entity or case nodes "
            "have not yet been projected to Neo4j via the CDC pipeline. "
            "Start the CDC worker, let it drain the outbox, then re-run this script."
        )
        sys.exit(1)
    else:
        logger.info("All rows projected successfully.")


if __name__ == "__main__":
    main()
