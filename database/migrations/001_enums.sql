-- =============================================================================
-- CIVIX Platform — Migration 001: ENUM Types
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/03_DATABASE_SCHEMA_BIBLE.md §ENUM Types (Migration 02)
--            BLK-01 Resolution: ADR-012 (five previously missing ENUMs)
-- =============================================================================
-- IDEMPOTENT: NO — Run once on a fresh database.
-- To check if already applied: SELECT typname FROM pg_type WHERE typname LIKE '%_enum';
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- ENTITY & IDENTITY
-- ---------------------------------------------------------------------------

CREATE TYPE civix.entity_type_enum AS ENUM (
    'PERSON',
    'SOURCE_IDENTITY',
    'PHONE_NUMBER',
    'SIM',
    'DEVICE',
    'FINANCIAL_ACCOUNT',
    'VEHICLE',
    'PROPERTY',
    'ORGANIZATION',
    'NETWORK',
    'LOCATION'
);

CREATE TYPE civix.source_identity_type_enum AS ENUM (
    'NAME',
    'PHONE_MSISDN',
    'IMEI',
    'MAC_ADDRESS',
    'VEHICLE_REG',
    'EMAIL',
    'FACE_EMBEDDING_REF',
    'FINGERPRINT_REF',
    'VOICE_PRINT_REF',
    'AADHAAR_MASKED',
    'PAN_MASKED',
    'DRIVING_LICENSE',
    'PASSPORT_NUMBER',
    'OTHER'
);

CREATE TYPE civix.identity_resolution_status_enum AS ENUM (
    'ACCEPTED',
    'REJECTED',
    'SUPERSEDED',
    'UNRESOLVED',
    'REVIEW_REQUIRED'
);

-- ---------------------------------------------------------------------------
-- EPISTEMIC PIPELINE
-- ---------------------------------------------------------------------------

CREATE TYPE civix.predicate_enum AS ENUM (
    'CALLED',
    'MESSAGED',
    'PINGED_TOWER',
    'USED_DEVICE',
    'USED_SIM',
    'HAD_NUMBER',
    'SEEN_AT',
    'PRESENT_AT',
    'TRANSFERRED_TO',
    'TRANSFERRED_FROM',
    'HOLDS_ACCOUNT',
    'OWNS',
    'OWNED',
    'TRANSFERRED_OWNERSHIP_OF',
    'RECEIVED_PROPERTY',
    'REGISTERED_TO',
    'DRIVER_OF',
    'PASSENGER_IN',
    'MEMBER_OF',
    'EMPLOYED_BY',
    'KNOWN_ASSOCIATE_OF',
    'RESIDED_AT',
    'VISITED',
    'ALIBI_CONFIRMED_AT',
    'DNA_MATCHES',
    'DNA_EXCLUDED',
    'FINGERPRINT_MATCHES',
    'FINGERPRINT_EXCLUDED',
    'FACE_MATCHES',
    'VEHICLE_REG_MATCHES',
    'TIME_OF_DEATH_IS',
    'CAUSE_OF_DEATH_IS',
    'HAS_INJURY',
    'LOCATED_AT',
    'REGISTERED_AT'
);
-- INVARIANT (INV-18): Free-text predicates are BANNED.
-- Only values in this ENUM are permitted. Enforce at application layer too.

CREATE TYPE civix.participant_role_enum AS ENUM (
    'CALLER',
    'CALLEE',
    'PING_SOURCE',
    'DRIVER',
    'PASSENGER',
    'REGISTERED_OWNER',
    'SENDER',
    'RECEIVER',
    'ACCOUNT_HOLDER',
    'JOINT_HOLDER',
    'BENEFICIARY',
    'PREVIOUS_OWNER',
    'NEW_OWNER',
    'TARGET_PROPERTY',
    'REGISTRAR',
    'LOCATION',
    'CELL_TOWER',
    'VICTIM',
    'SUSPECT',
    'WITNESS',
    'OFFICER',
    'OBSERVER',
    'SUBJECT',
    'COMPLAINANT',
    'SAMPLE_COLLECTOR',
    'EXAMINER',
    'CUSTODIAN',
    'PARTICIPANT'
);

CREATE TYPE civix.epistemic_status_enum AS ENUM (
    'POSSIBLE',
    'PROBABLE',
    'CONFIRMED',
    'REFUTED',
    'INCONCLUSIVE'
);

CREATE TYPE civix.support_stance_enum AS ENUM (
    'SUPPORT',
    'CONTRADICT',
    'NEUTRAL',
    'INCONCLUSIVE'
);
-- INVARIANT (INV-01): Stance lives ONLY in hypothesis_support.
-- Assertion has NO stance column.

CREATE TYPE civix.event_type_enum AS ENUM (
    'CALL',
    'MESSAGE',
    'TRANSACTION',
    'VEHICLE_SIGHTING',
    'PROPERTY_MUTATION',
    'MEETING',
    'SEIZURE',
    'ARREST',
    'SURVEILLANCE_OBSERVATION',
    'FORENSIC_COLLECTION',
    'MEDICAL_EXAMINATION',
    'FIR_FILING',
    'DEVICE_PING',
    'BORDER_CROSSING',
    'OTHER'
);

CREATE TYPE civix.extraction_type_enum AS ENUM (
    'FACE_DETECTION',
    'OCR',
    'ANPR',
    'NER',
    'RELATIONSHIP_EXTRACTION',
    'ANOMALY_DETECTION',
    'CLUSTERING',
    'VOICE_PRINT',
    'FINGERPRINT_MATCH',
    'GEOLOCATION_INFERENCE',
    'TEMPORAL_INFERENCE',
    'OTHER'
);

-- ---------------------------------------------------------------------------
-- CASE MANAGEMENT
-- ---------------------------------------------------------------------------

CREATE TYPE civix.case_type_enum AS ENUM (
    'CRIMINAL',
    'INTELLIGENCE',
    'PROPERTY',
    'FINANCIAL',
    'SURVEILLANCE',
    'FORENSIC',
    'MULTI_CASE'
);

CREATE TYPE civix.case_status_enum AS ENUM (
    'OPEN',
    'ACTIVE',
    'SUSPENDED',
    'CLOSED_SOLVED',
    'CLOSED_UNSOLVED',
    'ARCHIVED'
);

CREATE TYPE civix.case_priority_enum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);

CREATE TYPE civix.case_entity_role_enum AS ENUM (
    'SUSPECT',
    'VICTIM',
    'COMPLAINANT',
    'WITNESS',
    'PERSON_OF_INTEREST',
    'ACCUSED',
    'ACQUITTED',
    'OFFICER_IN_CHARGE',
    'INFORMANT',
    'SUBJECT_ORG',
    'SUBJECT_VEHICLE',
    'SUBJECT_ACCOUNT',
    'SUBJECT_PROPERTY',
    'SUBJECT_DEVICE',
    'RELATED_PERSON'
);

CREATE TYPE civix.case_permission_enum AS ENUM (
    'READ',
    'WRITE',
    'ADMIN'
);

-- ---------------------------------------------------------------------------
-- USERS & ACCESS
-- ---------------------------------------------------------------------------

CREATE TYPE civix.civix_role_enum AS ENUM (
    'INVESTIGATOR',
    'SUPERVISOR',
    'ANALYST',
    'ADMIN',
    'FORENSIC_EXAMINER',
    'LEGAL_OFFICER',
    'READ_ONLY'
);

CREATE TYPE civix.clearance_enum AS ENUM (
    'UNCLASSIFIED',
    'RESTRICTED',
    'CONFIDENTIAL',
    'SECRET'
);

-- ---------------------------------------------------------------------------
-- EVIDENCE & PROVENANCE
-- ---------------------------------------------------------------------------

CREATE TYPE civix.hash_algorithm_enum AS ENUM (
    'SHA256',
    'SHA512',
    'SHA3_256',
    'MD5_DEPRECATED'
);

CREATE TYPE civix.location_type_enum AS ENUM (
    'EXACT_POINT',
    'ESTIMATED_POINT',
    'CELL_SECTOR_POLYGON',
    'CCTV_COVERAGE_POLYGON',
    'PROPERTY_BOUNDARY',
    'CRIME_SCENE',
    'GEOFENCE',
    'ADMIN_BOUNDARY',
    'ROUTE_LINESTRING'
);

-- ---------------------------------------------------------------------------
-- LEGAL & AUDIT
-- ---------------------------------------------------------------------------

CREATE TYPE civix.audit_action_enum AS ENUM (
    'LOGIN',
    'LOGOUT',
    'READ',
    'WRITE',
    'EXPORT',
    'RESTRICT',
    'LIFT_RESTRICTION',
    'IDENTITY_RESOLVE',
    'HYPOTHESIS_STATUS_CHANGE',
    'LEAD_DISPOSITION',
    'ADMIN_ACTION',
    'TOMBSTONE_ISSUED'
);

CREATE TYPE civix.legal_restriction_type_enum AS ENUM (
    'EXPUNGED',
    'SEALED',
    'JUVENILE_PROTECTED',
    'COURT_RESTRICTED',
    'CLASSIFIED',
    'NATIONAL_SECURITY'
);

CREATE TYPE civix.data_quality_issue_type_enum AS ENUM (
    'IMPOSSIBLE_TIMESTAMP',
    'MALFORMED_RECORD',
    'DUPLICATE_RECORD',
    'MISSING_REQUIRED_FIELD',
    'CONTRADICTORY_DATA',
    'CUSTODY_GAP',
    'UNKNOWN_IDENTIFIER',
    'HASH_MISMATCH',
    'SPATIAL_IMPOSSIBILITY',
    'TEMPORAL_IMPOSSIBILITY',
    'OTHER'
);

-- ---------------------------------------------------------------------------
-- SYNTHETIC DATA CONTROL
-- ---------------------------------------------------------------------------

CREATE TYPE civix.dataset_type_enum AS ENUM (
    'GOLDEN_WORLD',
    'SYNTHETIC_TRAIN',
    'SYNTHETIC_VAL',
    'SYNTHETIC_TEST',
    'PRODUCTION'
);

-- ---------------------------------------------------------------------------
-- BLK-01 RESOLUTION (ADR-012): Five previously missing ENUMs
-- Authority: BLOCKER_RESOLUTION_LOG.md, CIVIX_CHANGE_CONTROL.md ADR-012
-- ---------------------------------------------------------------------------

CREATE TYPE civix.hypothesis_status_enum AS ENUM (
    'ACTIVE',         -- Default: under evaluation
    'UNDER_REVIEW',   -- Escalated to supervisor for second opinion
    'CONFIRMED',      -- Human-authorized conclusion (CHECK: confirmed_by IS NOT NULL)
    'REFUTED',        -- Definitively disproven; requires documented basis
    'ARCHIVED'        -- Administratively closed; may be reopened
);
-- NOTE: AI may NOT set status = 'CONFIRMED'. DB CHECK constraint enforces this.

CREATE TYPE civix.lead_priority_enum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);

CREATE TYPE civix.lead_status_enum AS ENUM (
    'OPEN',           -- Created; awaiting assignment (default)
    'IN_PROGRESS',    -- Actively being investigated
    'CONFIRMED',      -- Lead was valid; led to confirmed finding
    'FALSE_POSITIVE', -- Lead was invalid (required for FL-06 Rekha Verma test)
    'CLOSED',         -- Administratively closed without definitive resolution
    'DEFERRED'        -- Postponed; to be reviewed later
);

CREATE TYPE civix.task_type_enum AS ENUM (
    'INTERVIEW',
    'SURVEILLANCE',
    'SEARCH_AND_SEIZURE',
    'FORENSIC_COLLECTION',
    'FINANCIAL_REVIEW',
    'LEGAL_REQUEST',
    'COURT_ORDER',
    'DATA_ANALYSIS',
    'FIELD_VERIFICATION',
    'OTHER'
);

CREATE TYPE civix.task_status_enum AS ENUM (
    'PENDING',      -- Default: task created, not started
    'ASSIGNED',     -- Assigned to an investigator
    'IN_PROGRESS',  -- Work underway
    'COMPLETED',    -- Matches completed_at TIMESTAMPTZ
    'CANCELLED',
    'BLOCKED'       -- Cannot proceed; awaiting external dependency
);

-- =============================================================================
-- VALIDATION QUERY
-- =============================================================================
-- SELECT count(*) FROM pg_type WHERE typname LIKE '%_enum' AND typnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'civix');
-- Expected: 28
