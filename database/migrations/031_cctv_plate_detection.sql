-- =============================================================================
-- CIVIX Platform — Migration 031: CCTV Plate Detection
-- Phase E Implementation
-- =============================================================================

SET search_path TO civix, public;

CREATE TABLE IF NOT EXISTS civix.cctv_plate_detection (
    plate_detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES civix.cctv_search_job(job_id) ON DELETE CASCADE,
    camera_id UUID NOT NULL REFERENCES civix.cctv_camera(camera_id),
    track_id UUID NOT NULL REFERENCES civix.cctv_track(track_id) ON DELETE CASCADE,
    detection_id UUID REFERENCES civix.cctv_detection(detection_id) ON DELETE CASCADE,
    frame_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    bounding_box JSONB NOT NULL,
    plate_crop_storage_uri TEXT NOT NULL,
    raw_ocr_text TEXT NOT NULL,
    normalized_plate TEXT NOT NULL,
    ocr_confidence DOUBLE PRECISION NOT NULL,
    confidence_category TEXT NOT NULL CHECK (confidence_category IN ('HIGH', 'MEDIUM', 'LOW')),
    detector_model TEXT NOT NULL DEFAULT 'OpenCVPlateDetector/v1.0',
    ocr_engine TEXT NOT NULL DEFAULT 'LocalStructuralOCR/v1.0',
    ocr_engine_version TEXT NOT NULL DEFAULT '1.0.0',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_cctv_plate_detection_idempotency UNIQUE (job_id, track_id, raw_ocr_text)
);

CREATE INDEX IF NOT EXISTS idx_cctv_plate_detection_job_id ON civix.cctv_plate_detection(job_id);
CREATE INDEX IF NOT EXISTS idx_cctv_plate_detection_track_id ON civix.cctv_plate_detection(track_id);

-- RLS Policy
ALTER TABLE civix.cctv_plate_detection ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'cctv_plate_detection_rls') THEN
        CREATE POLICY cctv_plate_detection_rls ON civix.cctv_plate_detection FOR ALL USING (
            EXISTS (
                SELECT 1 FROM civix.cctv_search_job j
                JOIN civix.case_access ca ON ca.case_id = j.case_id
                WHERE j.job_id = cctv_plate_detection.job_id
                AND ca.user_id = current_setting('civix.current_user_id', true)::uuid
                AND ca.is_revoked = false
            )
        );
    END IF;
END $$;
