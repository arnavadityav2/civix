import time
import logging
import psycopg
import os
import json

from civix_api.services.cv.video_processor import VideoProcessor
from civix_api.services.cv.artifact_manager import ArtifactManager
from civix_api.services.cv.plate_detector import OpenCVPlateDetector
from civix_api.services.cv.plate_ocr import LocalPlateOCR

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class CCTVWorker:
    def __init__(self, pg_dsn: str):
        self.pg_dsn = pg_dsn
        self._running = False
        
        # Initialize CV pipeline foundation & Phase E extensions
        self.video_processor = VideoProcessor()
        self.artifact_manager = ArtifactManager()
        self.plate_detector = OpenCVPlateDetector()
        self.plate_ocr = LocalPlateOCR()

    def start(self):
        self._running = True
        logger.info("CCTV Worker (Phase B) started")
        while self._running:
            try:
                processed = self.process_next_job()
                if not processed:
                    time.sleep(1) # fallback polling
            except Exception as e:
                logger.error(f"CCTV Worker encountered unhandled error: {e}")
                time.sleep(2)

    def stop(self):
        self._running = False
        logger.info("CCTV Worker stopped")

    def process_next_job(self) -> bool:
        """Returns True if a job was processed, False if queue is empty."""
        try:
            with psycopg.connect(self.pg_dsn, autocommit=False) as conn:
                with conn.cursor() as cur:
                    # 1. Claim job using SKIP LOCKED
                    cur.execute("""
                        SELECT job_id, case_id, target_vehicle_id, camera_ids 
                        FROM civix.cctv_search_job
                        WHERE status = 'QUEUED'
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    """)
                    row = cur.fetchone()
                    
                    if not row:
                        return False
                    
                    job_id, case_id, target_vehicle_id, camera_ids = row
                    logger.info(f"Claimed CCTV job {job_id} for case {case_id}")
                    
                    try:
                        # 2. Mark RUNNING
                        cur.execute("UPDATE civix.cctv_search_job SET status = 'RUNNING', updated_at = NOW() WHERE job_id = %s", (job_id,))
                        conn.commit()
                        
                        # 3. Phase B: Real CV processing
                        total_frames_processed = 0
                        for idx, camera_id in enumerate(camera_ids):
                            # Get feed URL
                            cur.execute("SELECT feed_url FROM civix.cctv_feed WHERE camera_id = %s LIMIT 1", (camera_id,))
                            feed_row = cur.fetchone()
                            if not feed_row:
                                logger.warning(f"No active feed found for camera {camera_id}")
                                continue
                                
                            feed_url = feed_row[0]
                            # Handle local test fixture paths gracefully
                            if feed_url.startswith('file://'):
                                video_path = feed_url.replace('file://', '')
                            else:
                                video_path = feed_url
                                
                            logger.info(f"Processing feed for camera {camera_id} from {video_path}")
                            detections, tracks = self.video_processor.process_video(video_path, max_frames=500)
                            
                            # Persist Detections
                            for det in detections:
                                # For Phase B, we use a default timestamp (e.g., NOW) because frame_timestamp is required
                                # In production, this would be computed from the stream's start time and frame rate.
                                cur.execute("""
                                    INSERT INTO civix.cctv_detection 
                                    (job_id, camera_id, frame_timestamp, bounding_box, confidence)
                                    VALUES (%s, %s, NOW(), %s, %s)
                                """, (
                                    job_id, camera_id, 
                                    json.dumps(det.bounding_box), det.confidence
                                ))
                            
                            # Persist Tracks, Vehicle Artifacts, and Plate Signals
                            for track in tracks:
                                # Save vehicle crop artifact
                                crop_uri = self.artifact_manager.save_track_crop(track, str(job_id))
                                
                                cur.execute("""
                                    INSERT INTO civix.cctv_track
                                    (job_id, camera_id, track_uuid, first_seen, last_seen, crop_storage_uri, detected_make)
                                    VALUES (%s, %s, %s, NOW(), NOW(), %s, %s)
                                    RETURNING track_id
                                """, (
                                    job_id, camera_id, track.track_id, crop_uri, track.object_class
                                ))
                                track_db_id = cur.fetchone()[0]
                                
                                # Phase E: License Plate Detection & OCR
                                if track.best_crop is not None and track.best_crop.size > 0:
                                    plate_res = self.plate_detector.detect_plate(track.best_crop)
                                    if plate_res is not None:
                                        plate_crop_uri = self.artifact_manager.save_plate_crop(plate_res.plate_crop, str(job_id), str(track.track_id))
                                        ocr_res = self.plate_ocr.read_plate(plate_res.plate_crop)
                                        
                                        if plate_crop_uri and ocr_res.raw_ocr_text:
                                            cur.execute("""
                                                INSERT INTO civix.cctv_plate_detection (
                                                    job_id, camera_id, track_id, frame_timestamp, bounding_box,
                                                    plate_crop_storage_uri, raw_ocr_text, normalized_plate,
                                                    ocr_confidence, confidence_category, detector_model, ocr_engine, ocr_engine_version
                                                ) VALUES (
                                                    %s, %s, %s, NOW(), %s, %s, %s, %s, %s, %s, %s, %s, %s
                                                ) ON CONFLICT (job_id, track_id, raw_ocr_text) DO NOTHING
                                            """, (
                                                job_id, camera_id, track_db_id, json.dumps(plate_res.bounding_box),
                                                plate_crop_uri, ocr_res.raw_ocr_text, ocr_res.normalized_plate,
                                                ocr_res.confidence, ocr_res.confidence_category,
                                                self.plate_detector.model_name, ocr_res.ocr_engine, ocr_res.ocr_engine_version
                                            ))
                                
                            total_frames_processed += 500 # Simplified
                            
                            # Update progress
                            pct = int(((idx + 1) / len(camera_ids)) * 100)
                            cur.execute("""
                                UPDATE civix.cctv_search_job 
                                SET progress_pct = %s, frames_processed = %s, updated_at = NOW() 
                                WHERE job_id = %s
                            """, (pct, total_frames_processed, job_id))
                            conn.commit()

                        # 4. Mark COMPLETED
                        cur.execute("UPDATE civix.cctv_search_job SET status = 'COMPLETED', progress_pct = 100, updated_at = NOW() WHERE job_id = %s", (job_id,))
                        conn.commit()
                        logger.info(f"Successfully processed CCTV job {job_id}")
                        return True
                        
                    except Exception as e:
                        logger.warning(f"Error executing CCTV job {job_id}: {type(e).__name__} - {str(e)}")
                        conn.rollback()
                        self.handle_failure(job_id, str(e))
                        return True
        except psycopg.OperationalError as oe:
            logger.error(f"PostgreSQL connection error: {oe}")
            return False

    def handle_failure(self, job_id, error_msg):
        safe_error = error_msg[:500]
        try:
            with psycopg.connect(self.pg_dsn, autocommit=False) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE civix.cctv_search_job 
                        SET status = 'FAILED', 
                            error_message = %s,
                            updated_at = NOW()
                        WHERE job_id = %s
                    """, (safe_error, job_id))
                    logger.info(f"Marked CCTV job {job_id} as FAILED")
                    conn.commit()
        except Exception as e:
            logger.error(f"Failed to update error state for job {job_id}: {e}")

if __name__ == "__main__":
    pg_dsn = os.getenv("CIVIX_DATABASE_URL", "postgresql://civix_api:cHoOG4PMDTdWzqTSuOWAeGbt_In-lBhx@localhost:5433/civix_test").replace("+asyncpg", "")
    
    worker = CCTVWorker(pg_dsn)
    try:
        worker.start()
    except KeyboardInterrupt:
        worker.stop()
