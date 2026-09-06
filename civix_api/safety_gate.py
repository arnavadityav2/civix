import os
import sys
import logging
from urllib.parse import urlparse

logger = logging.getLogger("civix_api.safety_gate")

def verify_demo_environment_safety_gate():
    """
    Hard Safety Gate for CIVIX 2.0 FastAPI Application.
    Enforces strict environment isolation and Golden World protection.
    """
    from civix_api.config import settings
    
    civix_env = os.environ.get("CIVIX_ENV", settings.civix_env).lower()
    
    if civix_env != "demo":
        logger.error(f"[HARD ABORT] Invalid CIVIX_ENV='{civix_env}'. Expected 'demo'.")
        raise RuntimeError(f"Safety Gate Violation: CIVIX_ENV must strictly be 'demo'.")

    db_url = settings.civix_database_url or os.environ.get("CIVIX_DATABASE_URL", "")
    if "civix_demo" not in db_url:
        logger.error(f"[HARD ABORT] Database target violation: CIVIX_DATABASE_URL does not target 'civix_demo'. (Actual: {db_url})")
        raise RuntimeError("Safety Gate Violation: PostgreSQL target must be 'civix_demo'. Refusing to start against non-demo DB.")

    if "civix_test" in db_url:
        logger.error("[HARD ABORT] Golden World protection triggered: Attempted to run API against 'civix_test'!")
        raise RuntimeError("Golden World Protection Gate: Writing or running against civix_test is strictly forbidden in Demo mode.")

    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7688")
    if ":7688" not in neo4j_uri and ":7687" not in neo4j_uri:
        logger.error(f"[HARD ABORT] Neo4j target violation: NEO4J_URI port must be 7688 or 7687. (Actual: {neo4j_uri})")
        raise RuntimeError(f"Safety Gate Violation: Neo4j target must be isolated Demo port 7688 or 7687. Refusing to connect to {neo4j_uri}.")


    evidence_path = os.environ.get("CIVIX_EVIDENCE_STORE_PATH", r"c:\data\civix_demo\evidence_store")
    if "civix_demo" not in evidence_path.lower():
        logger.error(f"[HARD ABORT] Evidence path violation: Path outside Demo root. (Actual: {evidence_path})")
        raise RuntimeError("Safety Gate Violation: Demo evidence path must reside within Demo root.")

    cctv_path = os.environ.get("CIVIX_CCTV_ARTIFACT_PATH", r"c:\data\civix_demo\cctv_artifacts")
    if "civix_demo" not in cctv_path.lower():
        logger.error(f"[HARD ABORT] CCTV artifact path violation: Path outside Demo root. (Actual: {cctv_path})")
        raise RuntimeError("Safety Gate Violation: Demo CCTV artifact path must reside within Demo root.")

    logger.info("==========================================================================")
    logger.info("                  CIVIX 2.0 STARTUP SAFETY GATE PASSED                  ")
    logger.info("==========================================================================")
    logger.info("  CIVIX ENVIRONMENT : DEMO")
    logger.info(f"  PostgreSQL Target : civix_demo")
    logger.info(f"  Neo4j Target      : {neo4j_uri}")
    logger.info(f"  Evidence Root     : {evidence_path}")
    logger.info(f"  CCTV Artifact Root: {cctv_path}")
    logger.info("==========================================================================")

if __name__ == "__main__":
    verify_demo_environment_safety_gate()
