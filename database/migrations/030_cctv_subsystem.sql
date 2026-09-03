-- =============================================================================
-- CIVIX Platform — Migration 030: CCTV Intelligence Subsystem
-- Phase A Implementation
-- Authority: Final CCTV Implementation Contract
-- =============================================================================
-- Adds the 8 additive CCTV tables:
-- 1. cctv_source
-- 2. cctv_camera
-- 3. cctv_feed
-- 4. cctv_search_job
-- 5. cctv_detection
-- 6. cctv_track
-- 7. cctv_match_candidate
-- 8. cctv_observation
-- Includes RLS policies and validation logic.
-- =============================================================================

SET search_path TO civix, public;

-- 1. CCTV Source
CREATE TABLE IF NOT EXISTS civix.cctv_source (
    source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_name TEXT NOT NULL UNIQUE,
    operator_name TEXT NOT NULL,
    website_url TEXT,
    source_type TEXT NOT NULL CHECK (source_type IN ('PUBLIC_MUNICIPAL', 'PUBLIC_TRANSIT', 'PUBLIC_WEBCAM', 'SIMULATED_DEMO')),
    verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED' CHECK (verification_status IN ('VERIFIED', 'UNVERIFIED', 'DEPRECATED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. CCTV Camera
CREATE TABLE IF NOT EXISTS civix.cctv_camera (
    camera_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES civix.cctv_source(source_id) ON DELETE CASCADE,
    camera_code TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    city TEXT NOT NULL DEFAULT 'Delhi NCR',
    region TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    geometry GEOMETRY(Point, 4326),
    camera_type TEXT NOT NULL CHECK (camera_type IN ('FIXED_TRAFFIC', 'PTZ_SURVEILLANCE', 'DASHCAM', 'PLAZA_TOLL')),
    status TEXT NOT NULL DEFAULT 'OFFLINE' CHECK (status IN ('LIVE', 'REGISTERED_ONLY', 'OFFLINE', 'MAINTENANCE')),
    access_type TEXT NOT NULL CHECK (access_type IN ('PUBLIC_LIVE', 'PUBLIC_FRAME', 'AUTHORIZED', 'REGISTRY_ONLY', 'SIMULATED')),
    last_health_check TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. CCTV Feed
CREATE TABLE IF NOT EXISTS civix.cctv_feed (
    feed_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    camera_id UUID NOT NULL REFERENCES civix.cctv_camera(camera_id) ON DELETE CASCADE,
    feed_type TEXT NOT NULL CHECK (feed_type IN ('HLS', 'RTSP', 'MJPEG', 'SNAPSHOT_POLL', 'YOUTUBE_LIVE_EMBED')),
    feed_url TEXT NOT NULL,
    embed_url TEXT,
    frame_rate INT DEFAULT 15,
    resolution_w INT DEFAULT 1920,
    resolution_h INT DEFAULT 1080,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. CCTV Search Job (Async Worker State)
CREATE TABLE IF NOT EXISTS civix.cctv_search_job (
    job_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES civix.investigative_case(case_id) ON DELETE CASCADE,
    requested_by UUID NOT NULL REFERENCES civix.civix_user(user_id),
    target_vehicle_id UUID NOT NULL REFERENCES civix.vehicle(entity_id),
    camera_ids UUID[] NOT NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED' CHECK (status IN ('QUEUED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED', 'TIMED_OUT')),
    progress_pct INT NOT NULL DEFAULT 0,
    frames_processed INT NOT NULL DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. CCTV Detection (PostgreSQL Only - Single Frame Raw)
CREATE TABLE IF NOT EXISTS civix.cctv_detection (
    detection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES civix.cctv_search_job(job_id) ON DELETE CASCADE,
    camera_id UUID NOT NULL REFERENCES civix.cctv_camera(camera_id),
    frame_timestamp TIMESTAMPTZ NOT NULL,
    bounding_box JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. CCTV Track (PostgreSQL Only - Isolated)
CREATE TABLE IF NOT EXISTS civix.cctv_track (
    track_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES civix.cctv_search_job(job_id) ON DELETE CASCADE,
    camera_id UUID NOT NULL REFERENCES civix.cctv_camera(camera_id),
    track_uuid TEXT NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    best_plate_number TEXT,
    best_plate_confidence DOUBLE PRECISION,
    detected_make TEXT,
    detected_model TEXT,
    detected_color TEXT,
    detected_body_type TEXT,
    crop_storage_uri TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. CCTV Match Candidate (PostgreSQL Only)
CREATE TABLE IF NOT EXISTS civix.cctv_match_candidate (
    candidate_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES civix.cctv_search_job(job_id) ON DELETE CASCADE,
    track_id UUID NOT NULL REFERENCES civix.cctv_track(track_id) ON DELETE CASCADE,
    case_id UUID NOT NULL REFERENCES civix.investigative_case(case_id),
    target_vehicle_id UUID NOT NULL REFERENCES civix.vehicle(entity_id),
    signal_class TEXT NOT NULL CHECK (signal_class IN ('EXACT_PLATE_MATCH', 'PARTIAL_PLATE_MATCH', 'MODEL_ATTRIBUTE_MATCH', 'VISUAL_SIMILARITY')),
    overall_signal TEXT NOT NULL CHECK (overall_signal IN ('HIGH', 'MODERATE', 'LOW', 'NONE')),
    plate_match_type TEXT NOT NULL CHECK (plate_match_type IN ('EXACT', 'PARTIAL', 'NONE', 'UNAVAILABLE')),
    plate_confidence DOUBLE PRECISION,
    make_match BOOLEAN NOT NULL DEFAULT false,
    model_match BOOLEAN NOT NULL DEFAULT false,
    color_match BOOLEAN NOT NULL DEFAULT false,
    body_match BOOLEAN NOT NULL DEFAULT false,
    visual_similarity_score DOUBLE PRECISION,
    explanation_notes TEXT NOT NULL,
    review_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (review_status IN ('PENDING', 'ACCEPTED', 'REJECTED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. CCTV Observation (Human Reviewed - Emits CDC Outbox Event)
CREATE TABLE IF NOT EXISTS civix.cctv_observation (
    observation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    candidate_id UUID NOT NULL REFERENCES civix.cctv_match_candidate(candidate_id),
    case_id UUID NOT NULL REFERENCES civix.investigative_case(case_id),
    camera_id UUID NOT NULL REFERENCES civix.cctv_camera(camera_id),
    track_id UUID NOT NULL REFERENCES civix.cctv_track(track_id),
    instance_id UUID NOT NULL REFERENCES civix.evidence_instance(instance_id),
    signal_class TEXT NOT NULL,
    reviewed_by UUID NOT NULL REFERENCES civix.civix_user(user_id),
    reviewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    investigator_notes TEXT,
    generation_run_id UUID
);

-- ---------------------------------------------------------------------------
-- RLS Policies
-- ---------------------------------------------------------------------------

ALTER TABLE civix.cctv_search_job ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.cctv_detection ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.cctv_match_candidate ENABLE ROW LEVEL SECURITY;
ALTER TABLE civix.cctv_observation ENABLE ROW LEVEL SECURITY;

DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'cctv_search_job_rls') THEN
        CREATE POLICY cctv_search_job_rls ON civix.cctv_search_job FOR ALL USING (
            EXISTS (
                SELECT 1 FROM civix.case_access ca
                WHERE ca.case_id = cctv_search_job.case_id
                AND ca.user_id = current_setting('civix.current_user_id', true)::uuid
                AND ca.is_revoked = false
            )
        );
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'cctv_detection_rls') THEN
        CREATE POLICY cctv_detection_rls ON civix.cctv_detection FOR ALL USING (
            EXISTS (
                SELECT 1 FROM civix.cctv_search_job j
                JOIN civix.case_access ca ON ca.case_id = j.case_id
                WHERE j.job_id = cctv_detection.job_id
                AND ca.user_id = current_setting('civix.current_user_id', true)::uuid
                AND ca.is_revoked = false
            )
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'cctv_match_candidate_rls') THEN
        CREATE POLICY cctv_match_candidate_rls ON civix.cctv_match_candidate FOR ALL USING (
            EXISTS (
                SELECT 1 FROM civix.case_access ca
                WHERE ca.case_id = cctv_match_candidate.case_id
                AND ca.user_id = current_setting('civix.current_user_id', true)::uuid
                AND ca.is_revoked = false
            )
        );
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'cctv_observation_rls') THEN
        CREATE POLICY cctv_observation_rls ON civix.cctv_observation FOR ALL USING (
            EXISTS (
                SELECT 1 FROM civix.case_access ca
                WHERE ca.case_id = cctv_observation.case_id
                AND ca.user_id = current_setting('civix.current_user_id', true)::uuid
                AND ca.is_revoked = false
            )
        );
    END IF;
END $$;

-- ---------------------------------------------------------------------------
-- Validation Block
-- ---------------------------------------------------------------------------
DO $$
DECLARE
    tbl_count INT;
BEGIN
    SELECT COUNT(*) INTO tbl_count
    FROM information_schema.tables
    WHERE table_schema = 'civix'
      AND table_name IN ('cctv_source', 'cctv_camera', 'cctv_feed', 'cctv_search_job', 'cctv_detection', 'cctv_track', 'cctv_match_candidate', 'cctv_observation');

    IF tbl_count != 8 THEN
        RAISE EXCEPTION 'Migration 030 FAILED: Expected 8 CCTV tables, found %', tbl_count;
    END IF;

    RAISE NOTICE 'Migration 030 VERIFIED OK: 8 CCTV tables created successfully.';
END;
$$;
