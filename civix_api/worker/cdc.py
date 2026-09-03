import time
import json
import logging
import psycopg
from neo4j import GraphDatabase
from neo4j.exceptions import ClientError, TransientError
from civix_api.services.neo4j_projection import Neo4jProjectionService

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class CDCWorker:
    def __init__(self, pg_dsn: str, neo4j_uri: str, neo4j_user: str, neo4j_pass: str):
        self.pg_dsn = pg_dsn
        self.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        self.projection_service = Neo4jProjectionService()
        self._running = False

    def start(self):
        self._running = True
        logger.info("CDC Worker started")
        while self._running:
            try:
                processed = self.process_next_event()
                if not processed:
                    time.sleep(1) # fallback polling
            except Exception as e:
                logger.error(f"Worker encountered unhandled error: {e}")
                time.sleep(2)

    def stop(self):
        self._running = False
        self.neo4j_driver.close()
        logger.info("CDC Worker stopped")

    def process_next_event(self) -> bool:
        """Returns True if an event was processed, False if queue is empty."""
        try:
            with psycopg.connect(self.pg_dsn, autocommit=False) as conn:
                with conn.cursor() as cur:
                    # 1. Claim event and acquire row+advisory lock
                    cur.execute("SELECT id, entity_id, action, entity_type, payload, seq_no, retry_count FROM civix.claim_next_outbox_event()")
                    row = cur.fetchone()
                    
                    if not row:
                        return False
                    
                    event_id, entity_id, action, entity_type, payload, seq_no, retry_count = row
                    logger.info(f"Claimed event {event_id} (seq: {seq_no}, retries: {retry_count}) for entity {entity_id}")
                    
                    try:
                        # 2. Project to Neo4j
                        with self.neo4j_driver.session() as session:
                            self.projection_service.project(session, action, entity_type, payload, seq_no)
                        
                        # 3. Mark consumed
                        cur.execute("UPDATE civix.outbox SET consumed_at = NOW() WHERE id = %s", (event_id,))
                        conn.commit()
                        logger.info(f"Successfully processed event {event_id}")
                        return True
                        
                    except Exception as e:
                        logger.warning(f"Error projecting event {event_id}: {type(e).__name__} - {str(e)}")
                        # Primary transaction rolls back automatically because of exception in psycopg context?
                        # We must explicitly rollback if we catch it inside the `with psycopg.connect` block.
                        # Wait, we are inside a try block, but we want to rollback the connection BEFORE doing transaction 2.
                        conn.rollback()
                        
                        self.handle_failure(event_id, str(e), retry_count)
                        return True
        except psycopg.OperationalError as oe:
            logger.error(f"PostgreSQL connection error: {oe}")
            return False

    def handle_failure(self, event_id, error_msg, current_retry_count):
        safe_error = error_msg[:500]
        new_retry_count = current_retry_count + 1
        is_permanent = new_retry_count >= 3
        
        try:
            with psycopg.connect(self.pg_dsn, autocommit=False) as conn:
                with conn.cursor() as cur:
                    if is_permanent:
                        cur.execute("""
                            UPDATE civix.outbox 
                            SET error_status = 'PERMANENT_FAILURE', 
                                error_message = %s,
                                retry_count = %s
                            WHERE id = %s AND consumed_at IS NULL
                        """, (safe_error, new_retry_count, event_id))
                        logger.info(f"Marked event {event_id} as PERMANENT_FAILURE after {new_retry_count} attempts")
                    else:
                        cur.execute("""
                            UPDATE civix.outbox 
                            SET error_message = %s,
                                retry_count = %s
                            WHERE id = %s AND consumed_at IS NULL
                        """, (safe_error, new_retry_count, event_id))
                        logger.info(f"Recorded transient failure for event {event_id}, retry_count={new_retry_count}")
                    conn.commit()
        except Exception as e:
            logger.error(f"Failed to update error state for event {event_id}: {e}")



if __name__ == "__main__":
    import os
    pg_dsn = os.getenv("CIVIX_DATABASE_URL_SYNC", "postgresql://civix_cdc_worker:cdc_worker_pass_123@localhost:5433/civix_test")
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
    
    worker = CDCWorker(pg_dsn, neo4j_uri, neo4j_user, neo4j_pass)
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
