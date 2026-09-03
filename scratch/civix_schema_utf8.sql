--
-- PostgreSQL database dump
--

\restrict fC4jAHZeroKohFvgYkAKaDGcDPddjcxSWPZ32vjTLH1QxA7k2KREx4LLuqpTazF

-- Dumped from database version 16.15
-- Dumped by pg_dump version 16.15

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: civix; Type: SCHEMA; Schema: -; Owner: postgres
--

CREATE SCHEMA civix;


ALTER SCHEMA civix OWNER TO postgres;

--
-- Name: audit_action_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.audit_action_enum OWNER TO postgres;

--
-- Name: case_entity_role_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.case_entity_role_enum OWNER TO postgres;

--
-- Name: case_permission_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_permission_enum AS ENUM (
    'READ',
    'WRITE',
    'ADMIN'
);


ALTER TYPE civix.case_permission_enum OWNER TO postgres;

--
-- Name: case_priority_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_priority_enum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE civix.case_priority_enum OWNER TO postgres;

--
-- Name: case_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_status_enum AS ENUM (
    'OPEN',
    'ACTIVE',
    'SUSPENDED',
    'CLOSED_SOLVED',
    'CLOSED_UNSOLVED',
    'ARCHIVED'
);


ALTER TYPE civix.case_status_enum OWNER TO postgres;

--
-- Name: case_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.case_type_enum AS ENUM (
    'CRIMINAL',
    'INTELLIGENCE',
    'PROPERTY',
    'FINANCIAL',
    'SURVEILLANCE',
    'FORENSIC',
    'MULTI_CASE'
);


ALTER TYPE civix.case_type_enum OWNER TO postgres;

--
-- Name: civix_role_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.civix_role_enum AS ENUM (
    'INVESTIGATOR',
    'SUPERVISOR',
    'ANALYST',
    'ADMIN',
    'FORENSIC_EXAMINER',
    'LEGAL_OFFICER',
    'READ_ONLY'
);


ALTER TYPE civix.civix_role_enum OWNER TO postgres;

--
-- Name: clearance_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.clearance_enum AS ENUM (
    'UNCLASSIFIED',
    'RESTRICTED',
    'CONFIDENTIAL',
    'SECRET'
);


ALTER TYPE civix.clearance_enum OWNER TO postgres;

--
-- Name: data_quality_issue_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.data_quality_issue_type_enum OWNER TO postgres;

--
-- Name: dataset_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.dataset_type_enum AS ENUM (
    'GOLDEN_WORLD',
    'SYNTHETIC_TRAIN',
    'SYNTHETIC_VAL',
    'SYNTHETIC_TEST',
    'PRODUCTION'
);


ALTER TYPE civix.dataset_type_enum OWNER TO postgres;

--
-- Name: entity_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.entity_type_enum OWNER TO postgres;

--
-- Name: epistemic_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.epistemic_status_enum AS ENUM (
    'POSSIBLE',
    'PROBABLE',
    'CONFIRMED',
    'REFUTED',
    'INCONCLUSIVE'
);


ALTER TYPE civix.epistemic_status_enum OWNER TO postgres;

--
-- Name: event_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.event_type_enum OWNER TO postgres;

--
-- Name: extraction_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.extraction_type_enum OWNER TO postgres;

--
-- Name: hash_algorithm_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.hash_algorithm_enum AS ENUM (
    'SHA256',
    'SHA512',
    'SHA3_256',
    'MD5_DEPRECATED'
);


ALTER TYPE civix.hash_algorithm_enum OWNER TO postgres;

--
-- Name: hypothesis_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.hypothesis_status_enum AS ENUM (
    'ACTIVE',
    'UNDER_REVIEW',
    'CONFIRMED',
    'REFUTED',
    'ARCHIVED'
);


ALTER TYPE civix.hypothesis_status_enum OWNER TO postgres;

--
-- Name: identity_resolution_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.identity_resolution_status_enum AS ENUM (
    'ACCEPTED',
    'REJECTED',
    'SUPERSEDED',
    'UNRESOLVED',
    'REVIEW_REQUIRED'
);


ALTER TYPE civix.identity_resolution_status_enum OWNER TO postgres;

--
-- Name: lead_priority_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.lead_priority_enum AS ENUM (
    'CRITICAL',
    'HIGH',
    'MEDIUM',
    'LOW'
);


ALTER TYPE civix.lead_priority_enum OWNER TO postgres;

--
-- Name: lead_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.lead_status_enum AS ENUM (
    'OPEN',
    'IN_PROGRESS',
    'CONFIRMED',
    'FALSE_POSITIVE',
    'CLOSED',
    'DEFERRED'
);


ALTER TYPE civix.lead_status_enum OWNER TO postgres;

--
-- Name: legal_restriction_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.legal_restriction_type_enum AS ENUM (
    'EXPUNGED',
    'SEALED',
    'JUVENILE_PROTECTED',
    'COURT_RESTRICTED',
    'CLASSIFIED',
    'NATIONAL_SECURITY'
);


ALTER TYPE civix.legal_restriction_type_enum OWNER TO postgres;

--
-- Name: location_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.location_type_enum OWNER TO postgres;

--
-- Name: participant_role_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.participant_role_enum OWNER TO postgres;

--
-- Name: predicate_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.predicate_enum OWNER TO postgres;

--
-- Name: source_identity_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.source_identity_type_enum OWNER TO postgres;

--
-- Name: support_stance_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.support_stance_enum AS ENUM (
    'SUPPORT',
    'CONTRADICT',
    'NEUTRAL',
    'INCONCLUSIVE'
);


ALTER TYPE civix.support_stance_enum OWNER TO postgres;

--
-- Name: task_status_enum; Type: TYPE; Schema: civix; Owner: postgres
--

CREATE TYPE civix.task_status_enum AS ENUM (
    'PENDING',
    'ASSIGNED',
    'IN_PROGRESS',
    'COMPLETED',
    'CANCELLED',
    'BLOCKED'
);


ALTER TYPE civix.task_status_enum OWNER TO postgres;

--
-- Name: task_type_enum; Type: TYPE; Schema: civix; Owner: postgres
--

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


ALTER TYPE civix.task_type_enum OWNER TO postgres;

--
-- Name: block_mutation(); Type: FUNCTION; Schema: civix; Owner: postgres
--

CREATE FUNCTION civix.block_mutation() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        RAISE EXCEPTION 'Updates and deletions are strictly forbidden on this immutable audit table.';
    END;
    $$;


ALTER FUNCTION civix.block_mutation() OWNER TO postgres;

--
-- Name: block_operational_delete(); Type: FUNCTION; Schema: civix; Owner: postgres
--

CREATE FUNCTION civix.block_operational_delete() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
    BEGIN
        IF OLD.generation_run_id IS NULL THEN
            RAISE EXCEPTION 'Operational deletion of non-synthetic records is strictly forbidden.';
        END IF;
        RETURN OLD;
    END;
    $$;


ALTER FUNCTION civix.block_operational_delete() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account_holder; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.account_holder (
    holder_id uuid DEFAULT gen_random_uuid() NOT NULL,
    account_id uuid NOT NULL,
    holder_entity_id uuid NOT NULL,
    holder_role text NOT NULL,
    ownership_percentage numeric(5,2),
    valid_time tstzrange NOT NULL,
    source_record_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT check_ownership_percentage CHECK (((ownership_percentage >= (0)::numeric) AND (ownership_percentage <= (100)::numeric)))
);


ALTER TABLE civix.account_holder OWNER TO postgres;

--
-- Name: analysis_run; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.analysis_run (
    run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    model_name text NOT NULL,
    model_version text NOT NULL,
    algorithm_type text NOT NULL,
    algorithm_parameters jsonb,
    input_snapshot_hash bytea,
    input_snapshot_tx_time timestamp with time zone,
    started_at timestamp with time zone NOT NULL,
    finished_at timestamp with time zone,
    initiated_by uuid,
    generation_run_id uuid
);


ALTER TABLE civix.analysis_run OWNER TO postgres;

--
-- Name: assertion; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.assertion (
    assertion_id uuid DEFAULT gen_random_uuid() NOT NULL,
    subject_entity_id uuid NOT NULL,
    predicate civix.predicate_enum NOT NULL,
    object_entity_id uuid,
    object_value text,
    object_location_id uuid,
    epistemic_status civix.epistemic_status_enum NOT NULL,
    ai_confidence numeric(5,4),
    asserted_by uuid,
    source_analysis_run_id uuid,
    valid_from timestamp with time zone,
    valid_to timestamp with time zone,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_assertion_confidence CHECK (((ai_confidence IS NULL) OR ((ai_confidence >= (0)::numeric) AND (ai_confidence <= (1)::numeric)))),
    CONSTRAINT chk_assertion_object CHECK (((object_entity_id IS NOT NULL) OR (object_value IS NOT NULL) OR (object_location_id IS NOT NULL))),
    CONSTRAINT chk_assertion_source CHECK (((asserted_by IS NOT NULL) OR (source_analysis_run_id IS NOT NULL)))
);


ALTER TABLE civix.assertion OWNER TO postgres;

--
-- Name: audit_event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.audit_event (
    audit_id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    action civix.audit_action_enum NOT NULL,
    target_table text NOT NULL,
    target_id uuid NOT NULL,
    case_context_id uuid,
    ip_address inet,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    metadata jsonb
);


ALTER TABLE civix.audit_event OWNER TO postgres;

--
-- Name: case_access; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.case_access (
    access_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    user_id uuid NOT NULL,
    permission_level civix.case_permission_enum NOT NULL,
    granted_by uuid NOT NULL,
    granted_at timestamp with time zone DEFAULT now() NOT NULL,
    valid_until timestamp with time zone,
    is_revoked boolean DEFAULT false NOT NULL,
    revoked_by uuid,
    revoked_at timestamp with time zone
);


ALTER TABLE civix.case_access OWNER TO postgres;

--
-- Name: case_entity_role; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.case_entity_role (
    role_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    entity_id uuid NOT NULL,
    role civix.case_entity_role_enum NOT NULL,
    role_basis text,
    assigned_by uuid,
    valid_from date,
    valid_to date,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.case_entity_role FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.case_entity_role OWNER TO postgres;

--
-- Name: case_link; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.case_link (
    link_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_case_id uuid NOT NULL,
    target_case_id uuid NOT NULL,
    linked_object_type text NOT NULL,
    linked_object_id uuid NOT NULL,
    share_scope text NOT NULL,
    authorized_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT chk_case_link_not_self CHECK ((source_case_id <> target_case_id))
);

ALTER TABLE ONLY civix.case_link FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.case_link OWNER TO postgres;

--
-- Name: civix_user; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.civix_user (
    user_id uuid DEFAULT gen_random_uuid() NOT NULL,
    external_auth_id text NOT NULL,
    username text NOT NULL,
    display_name text NOT NULL,
    role civix.civix_role_enum NOT NULL,
    clearance_level civix.clearance_enum DEFAULT 'UNCLASSIFIED'::civix.clearance_enum NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    department text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    last_login_at timestamp with time zone
);


ALTER TABLE civix.civix_user OWNER TO postgres;

--
-- Name: data_quality_issue; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.data_quality_issue (
    issue_id uuid DEFAULT gen_random_uuid() NOT NULL,
    affected_entity_type text NOT NULL,
    affected_entity_id uuid NOT NULL,
    issue_type civix.data_quality_issue_type_enum NOT NULL,
    severity text NOT NULL,
    detected_by text NOT NULL,
    detection_run_id uuid,
    detected_at timestamp with time zone DEFAULT now() NOT NULL,
    description text NOT NULL,
    status text DEFAULT 'OPEN'::text NOT NULL,
    resolution_notes text,
    resolved_by uuid,
    resolved_at timestamp with time zone
);


ALTER TABLE civix.data_quality_issue OWNER TO postgres;

--
-- Name: dataset; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.dataset (
    dataset_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    dataset_type civix.dataset_type_enum NOT NULL
);


ALTER TABLE civix.dataset OWNER TO postgres;

--
-- Name: device; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.device (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'DEVICE'::civix.entity_type_enum NOT NULL,
    imei character varying(17),
    mac_address character varying(17),
    device_type text NOT NULL,
    manufacturer text,
    model text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_device CHECK ((entity_type = 'DEVICE'::civix.entity_type_enum))
);


ALTER TABLE civix.device OWNER TO postgres;

--
-- Name: entity; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.entity (
    entity_id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_type civix.entity_type_enum NOT NULL,
    generation_run_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    created_by uuid
);


ALTER TABLE civix.entity OWNER TO postgres;

--
-- Name: event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.event (
    event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_type civix.event_type_enum NOT NULL,
    occurred_at tstzrange NOT NULL,
    description text,
    source_record_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.event OWNER TO postgres;

--
-- Name: event_participant; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.event_participant (
    participant_id uuid DEFAULT gen_random_uuid() NOT NULL,
    event_id uuid NOT NULL,
    entity_id uuid NOT NULL,
    participant_role civix.participant_role_enum NOT NULL,
    role_confidence numeric(5,4),
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.event_participant OWNER TO postgres;

--
-- Name: evidence_artifact; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.evidence_artifact (
    artifact_id uuid DEFAULT gen_random_uuid() NOT NULL,
    sha256_hash bytea NOT NULL,
    hash_algorithm civix.hash_algorithm_enum DEFAULT 'SHA256'::civix.hash_algorithm_enum NOT NULL,
    file_size_bytes bigint,
    mime_type text,
    original_filename text,
    storage_uri text,
    is_integrity_verified boolean DEFAULT false NOT NULL,
    acquired_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.evidence_artifact OWNER TO postgres;

--
-- Name: evidence_instance; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.evidence_instance (
    instance_id uuid DEFAULT gen_random_uuid() NOT NULL,
    artifact_id uuid NOT NULL,
    case_id uuid NOT NULL,
    source_record_id uuid,
    acquired_by uuid,
    acquisition_method text,
    acquisition_context text,
    legal_status text DEFAULT 'ACTIVE'::text NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.evidence_instance FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.evidence_instance OWNER TO postgres;

--
-- Name: extraction; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.extraction (
    extraction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    analysis_run_id uuid NOT NULL,
    extraction_type civix.extraction_type_enum NOT NULL,
    extracted_value jsonb NOT NULL,
    ai_confidence numeric(5,4) NOT NULL,
    is_superseded boolean DEFAULT false NOT NULL,
    superseded_by uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT chk_ai_confidence_ext CHECK (((ai_confidence >= (0)::numeric) AND (ai_confidence <= (1)::numeric)))
);

ALTER TABLE ONLY civix.extraction FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.extraction OWNER TO postgres;

--
-- Name: financial_account; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.financial_account (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'FINANCIAL_ACCOUNT'::civix.entity_type_enum NOT NULL,
    masked_number text NOT NULL,
    account_type text NOT NULL,
    bank_name text,
    ifsc_code character varying(11),
    currency character varying(3) DEFAULT 'INR'::character varying,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_financial_account CHECK ((entity_type = 'FINANCIAL_ACCOUNT'::civix.entity_type_enum))
);


ALTER TABLE civix.financial_account OWNER TO postgres;

--
-- Name: fir; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.fir (
    fir_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    fir_number text NOT NULL,
    police_station text NOT NULL,
    district text NOT NULL,
    filed_at timestamp with time zone NOT NULL,
    filed_by uuid,
    complainant_entity_id uuid,
    sections_invoked text[],
    source_record_id uuid,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.fir FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.fir OWNER TO postgres;

--
-- Name: forensic_report; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.forensic_report (
    report_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    report_type text NOT NULL,
    lab_name text,
    examiner_name text,
    findings_summary text,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.forensic_report FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.forensic_report OWNER TO postgres;

--
-- Name: generation_run; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.generation_run (
    generation_run_id uuid DEFAULT gen_random_uuid() NOT NULL,
    dataset_id uuid NOT NULL,
    scenario_id uuid NOT NULL,
    run_timestamp timestamp with time zone DEFAULT now() NOT NULL,
    world_seed bigint,
    generator_version text
);


ALTER TABLE civix.generation_run OWNER TO postgres;

--
-- Name: hypothesis; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.hypothesis (
    hypothesis_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    hypothesis_text text NOT NULL,
    status civix.hypothesis_status_enum DEFAULT 'ACTIVE'::civix.hypothesis_status_enum NOT NULL,
    created_by uuid NOT NULL,
    confirmed_by uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_hypothesis_status CHECK (((status <> 'CONFIRMED'::civix.hypothesis_status_enum) OR (confirmed_by IS NOT NULL)))
);

ALTER TABLE ONLY civix.hypothesis FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.hypothesis OWNER TO postgres;

--
-- Name: hypothesis_support; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.hypothesis_support (
    support_id uuid DEFAULT gen_random_uuid() NOT NULL,
    hypothesis_id uuid NOT NULL,
    assertion_id uuid NOT NULL,
    stance civix.support_stance_enum NOT NULL,
    weight numeric(5,4) DEFAULT 1.0 NOT NULL,
    assigned_by uuid,
    analysis_run_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.hypothesis_support FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.hypothesis_support OWNER TO postgres;

--
-- Name: identity_candidate; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_candidate (
    candidate_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_identity_id uuid NOT NULL,
    proposed_person_id uuid NOT NULL,
    ai_confidence numeric(5,4) NOT NULL,
    analysis_run_id uuid NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT chk_ai_confidence CHECK (((ai_confidence >= (0)::numeric) AND (ai_confidence <= (1)::numeric)))
);


ALTER TABLE civix.identity_candidate OWNER TO postgres;

--
-- Name: identity_merge_event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_merge_event (
    merge_event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_identity_a uuid NOT NULL,
    source_identity_b uuid NOT NULL,
    merged_into_person_id uuid NOT NULL,
    resolution_id uuid NOT NULL,
    decided_by uuid NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL,
    reason text
);


ALTER TABLE civix.identity_merge_event OWNER TO postgres;

--
-- Name: identity_resolution; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_resolution (
    resolution_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_identity_id uuid NOT NULL,
    candidate_id uuid,
    resolved_person_id uuid,
    status civix.identity_resolution_status_enum NOT NULL,
    decided_by uuid,
    decision_notes text,
    superseded_by uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    CONSTRAINT chk_identity_resolution_status CHECK (((status <> 'ACCEPTED'::civix.identity_resolution_status_enum) OR (resolved_person_id IS NOT NULL)))
);


ALTER TABLE civix.identity_resolution OWNER TO postgres;

--
-- Name: identity_split_event; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.identity_split_event (
    split_event_id uuid DEFAULT gen_random_uuid() NOT NULL,
    original_resolution_id uuid NOT NULL,
    split_source_identity_a uuid NOT NULL,
    split_source_identity_b uuid NOT NULL,
    new_person_b_id uuid NOT NULL,
    decided_by uuid NOT NULL,
    reason text NOT NULL,
    occurred_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.identity_split_event OWNER TO postgres;

--
-- Name: investigation_task; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.investigation_task (
    task_id uuid DEFAULT gen_random_uuid() NOT NULL,
    lead_id uuid,
    case_id uuid NOT NULL,
    task_type civix.task_type_enum NOT NULL,
    assigned_to uuid,
    status civix.task_status_enum DEFAULT 'PENDING'::civix.task_status_enum NOT NULL,
    due_date date,
    outcome_notes text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    completed_at timestamp with time zone,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.investigation_task FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.investigation_task OWNER TO postgres;

--
-- Name: investigative_case; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.investigative_case (
    case_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_number text NOT NULL,
    title text NOT NULL,
    case_type civix.case_type_enum NOT NULL,
    status civix.case_status_enum DEFAULT 'OPEN'::civix.case_status_enum NOT NULL,
    priority civix.case_priority_enum DEFAULT 'MEDIUM'::civix.case_priority_enum NOT NULL,
    jurisdiction text NOT NULL,
    investigating_unit text,
    opened_at date NOT NULL,
    closed_at date,
    lead_investigator_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid,
    CONSTRAINT chk_case_closed_date CHECK (((closed_at IS NULL) OR (closed_at >= opened_at)))
);

ALTER TABLE ONLY civix.investigative_case FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.investigative_case OWNER TO postgres;

--
-- Name: investigative_lead; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.investigative_lead (
    lead_id uuid DEFAULT gen_random_uuid() NOT NULL,
    case_id uuid NOT NULL,
    generated_by_run_id uuid,
    generated_by_person uuid,
    lead_text text NOT NULL,
    explanation text,
    priority civix.lead_priority_enum DEFAULT 'MEDIUM'::civix.lead_priority_enum NOT NULL,
    status civix.lead_status_enum DEFAULT 'OPEN'::civix.lead_status_enum NOT NULL,
    ai_confidence numeric(5,4),
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    disposition_notes text,
    disposed_by uuid,
    disposed_at timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_lead_generator CHECK (((generated_by_run_id IS NOT NULL) OR (generated_by_person IS NOT NULL)))
);

ALTER TABLE ONLY civix.investigative_lead FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.investigative_lead OWNER TO postgres;

--
-- Name: legal_restriction; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.legal_restriction (
    restriction_id uuid DEFAULT gen_random_uuid() NOT NULL,
    target_entity_id uuid,
    target_artifact_id uuid,
    restriction_type civix.legal_restriction_type_enum NOT NULL,
    authority text NOT NULL,
    court_order_reference text,
    effective_range tstzrange NOT NULL,
    scope text NOT NULL,
    status text DEFAULT 'ACTIVE'::text NOT NULL,
    created_by uuid NOT NULL,
    lifted_by uuid,
    lifted_at timestamp with time zone,
    CONSTRAINT chk_restriction_target CHECK (((target_entity_id IS NOT NULL) OR (target_artifact_id IS NOT NULL)))
);


ALTER TABLE civix.legal_restriction OWNER TO postgres;

--
-- Name: location; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.location (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'LOCATION'::civix.entity_type_enum NOT NULL,
    location_name text,
    location_type civix.location_type_enum NOT NULL,
    uncertainty_radius_meters double precision,
    altitude_meters double precision,
    azimuth_degrees double precision,
    beamwidth_degrees double precision,
    source_record_id uuid,
    generation_run_id uuid,
    geometry public.geometry(Geometry,4326) NOT NULL,
    CONSTRAINT chk_entity_type_location CHECK ((entity_type = 'LOCATION'::civix.entity_type_enum))
);


ALTER TABLE civix.location OWNER TO postgres;

--
-- Name: medical_report; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.medical_report (
    report_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    examination_type text NOT NULL,
    findings_summary text,
    practitioner_name text,
    examination_date date,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.medical_report FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.medical_report OWNER TO postgres;

--
-- Name: network; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.network (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'NETWORK'::civix.entity_type_enum NOT NULL,
    network_name text NOT NULL,
    network_type text NOT NULL,
    notes text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_network CHECK ((entity_type = 'NETWORK'::civix.entity_type_enum))
);


ALTER TABLE civix.network OWNER TO postgres;

--
-- Name: observation; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.observation (
    observation_id uuid DEFAULT gen_random_uuid() NOT NULL,
    instance_id uuid NOT NULL,
    observer_type text NOT NULL,
    observed_by uuid,
    observation_type text,
    observation_text text,
    structured_content jsonb,
    observed_at timestamp with time zone NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);

ALTER TABLE ONLY civix.observation FORCE ROW LEVEL SECURITY;


ALTER TABLE civix.observation OWNER TO postgres;

--
-- Name: organization; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.organization (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'ORGANIZATION'::civix.entity_type_enum NOT NULL,
    legal_name text NOT NULL,
    org_type text NOT NULL,
    registration_number text,
    incorporation_date date,
    jurisdiction text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_organization CHECK ((entity_type = 'ORGANIZATION'::civix.entity_type_enum))
);


ALTER TABLE civix.organization OWNER TO postgres;

--
-- Name: outbox; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.outbox (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    entity_id uuid NOT NULL,
    action text NOT NULL,
    entity_type text NOT NULL,
    payload jsonb NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    consumed_at timestamp with time zone
);


ALTER TABLE civix.outbox OWNER TO postgres;

--
-- Name: person; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.person (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'PERSON'::civix.entity_type_enum NOT NULL,
    display_name text NOT NULL,
    date_of_birth date,
    gender text,
    nationality character varying(3),
    is_deceased boolean DEFAULT false NOT NULL,
    deceased_at date,
    notes text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_person CHECK ((entity_type = 'PERSON'::civix.entity_type_enum))
);


ALTER TABLE civix.person OWNER TO postgres;

--
-- Name: person_alias; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.person_alias (
    alias_id uuid DEFAULT gen_random_uuid() NOT NULL,
    person_id uuid NOT NULL,
    alias_value text NOT NULL,
    alias_type text NOT NULL,
    source_record_id uuid,
    valid_from date,
    valid_to date,
    tx_start timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.person_alias OWNER TO postgres;

--
-- Name: phone_number; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.phone_number (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'PHONE_NUMBER'::civix.entity_type_enum NOT NULL,
    msisdn character varying(15) NOT NULL,
    country_code character varying(3) DEFAULT 'IND'::character varying,
    operator text,
    number_type text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_phone_number CHECK ((entity_type = 'PHONE_NUMBER'::civix.entity_type_enum))
);


ALTER TABLE civix.phone_number OWNER TO postgres;

--
-- Name: property; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.property (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'PROPERTY'::civix.entity_type_enum NOT NULL,
    property_ref text NOT NULL,
    property_type text NOT NULL,
    area_sqm numeric,
    description text,
    generation_run_id uuid,
    boundary_geometry public.geometry(Polygon,4326),
    CONSTRAINT chk_entity_type_property CHECK ((entity_type = 'PROPERTY'::civix.entity_type_enum))
);


ALTER TABLE civix.property OWNER TO postgres;

--
-- Name: provenance; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.provenance (
    provenance_id uuid DEFAULT gen_random_uuid() NOT NULL,
    derived_type text NOT NULL,
    derived_id uuid NOT NULL,
    source_type text NOT NULL,
    source_id uuid NOT NULL,
    derivation_method text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE civix.provenance OWNER TO postgres;

--
-- Name: scenario; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.scenario (
    scenario_id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    config_metadata json
);


ALTER TABLE civix.scenario OWNER TO postgres;

--
-- Name: sim; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.sim (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'SIM'::civix.entity_type_enum NOT NULL,
    iccid character varying(22) NOT NULL,
    imsi character varying(15),
    issuing_operator text,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_sim CHECK ((entity_type = 'SIM'::civix.entity_type_enum))
);


ALTER TABLE civix.sim OWNER TO postgres;

--
-- Name: sim_in_device; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.sim_in_device (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    sim_id uuid NOT NULL,
    device_id uuid NOT NULL,
    valid_time tstzrange NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.sim_in_device OWNER TO postgres;

--
-- Name: sim_number_assignment; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.sim_number_assignment (
    assignment_id uuid DEFAULT gen_random_uuid() NOT NULL,
    sim_id uuid NOT NULL,
    phone_number_id uuid NOT NULL,
    valid_time tstzrange NOT NULL,
    source_record_id uuid,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    generation_run_id uuid
);


ALTER TABLE civix.sim_number_assignment OWNER TO postgres;

--
-- Name: source; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.source (
    source_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_name text NOT NULL,
    agency_type text NOT NULL,
    reliability_score numeric(3,2),
    jurisdiction text,
    is_identity_protected boolean DEFAULT false NOT NULL,
    source_handler_id uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT check_reliability_score CHECK (((reliability_score >= 0.0) AND (reliability_score <= 1.0)))
);


ALTER TABLE civix.source OWNER TO postgres;

--
-- Name: source_identity; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.source_identity (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'SOURCE_IDENTITY'::civix.entity_type_enum NOT NULL,
    raw_identifier text NOT NULL,
    identifier_type civix.source_identity_type_enum NOT NULL,
    source_record_id uuid,
    observed_at timestamp with time zone NOT NULL,
    tx_start timestamp with time zone DEFAULT now() NOT NULL,
    tx_end timestamp with time zone,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_source_identity CHECK ((entity_type = 'SOURCE_IDENTITY'::civix.entity_type_enum))
);


ALTER TABLE civix.source_identity OWNER TO postgres;

--
-- Name: source_record; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.source_record (
    source_record_id uuid DEFAULT gen_random_uuid() NOT NULL,
    source_id uuid NOT NULL,
    external_reference text,
    record_type text NOT NULL,
    raw_content_hash bytea,
    received_at timestamp with time zone DEFAULT now() NOT NULL,
    superseded_by uuid,
    generation_run_id uuid
);


ALTER TABLE civix.source_record OWNER TO postgres;

--
-- Name: vehicle; Type: TABLE; Schema: civix; Owner: postgres
--

CREATE TABLE civix.vehicle (
    entity_id uuid NOT NULL,
    entity_type civix.entity_type_enum DEFAULT 'VEHICLE'::civix.entity_type_enum NOT NULL,
    registration_number text NOT NULL,
    vin text,
    make text,
    model text,
    color text,
    vehicle_type text NOT NULL,
    registration_year integer,
    generation_run_id uuid,
    CONSTRAINT chk_entity_type_vehicle CHECK ((entity_type = 'VEHICLE'::civix.entity_type_enum))
);


ALTER TABLE civix.vehicle OWNER TO postgres;

--
-- Name: account_holder account_holder_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_pkey PRIMARY KEY (holder_id);


--
-- Name: analysis_run analysis_run_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.analysis_run
    ADD CONSTRAINT analysis_run_pkey PRIMARY KEY (run_id);


--
-- Name: assertion assertion_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_pkey PRIMARY KEY (assertion_id);


--
-- Name: audit_event audit_event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.audit_event
    ADD CONSTRAINT audit_event_pkey PRIMARY KEY (audit_id);


--
-- Name: case_access case_access_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_pkey PRIMARY KEY (access_id);


--
-- Name: case_entity_role case_entity_role_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_pkey PRIMARY KEY (role_id);


--
-- Name: case_link case_link_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_pkey PRIMARY KEY (link_id);


--
-- Name: civix_user civix_user_external_auth_id_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.civix_user
    ADD CONSTRAINT civix_user_external_auth_id_key UNIQUE (external_auth_id);


--
-- Name: civix_user civix_user_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.civix_user
    ADD CONSTRAINT civix_user_pkey PRIMARY KEY (user_id);


--
-- Name: civix_user civix_user_username_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.civix_user
    ADD CONSTRAINT civix_user_username_key UNIQUE (username);


--
-- Name: data_quality_issue data_quality_issue_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.data_quality_issue
    ADD CONSTRAINT data_quality_issue_pkey PRIMARY KEY (issue_id);


--
-- Name: dataset dataset_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.dataset
    ADD CONSTRAINT dataset_pkey PRIMARY KEY (dataset_id);


--
-- Name: device device_imei_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_imei_key UNIQUE (imei);


--
-- Name: device device_mac_address_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_mac_address_key UNIQUE (mac_address);


--
-- Name: device device_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_pkey PRIMARY KEY (entity_id);


--
-- Name: entity entity_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT entity_pkey PRIMARY KEY (entity_id);


--
-- Name: event_participant event_participant_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_pkey PRIMARY KEY (participant_id);


--
-- Name: event event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event
    ADD CONSTRAINT event_pkey PRIMARY KEY (event_id);


--
-- Name: evidence_artifact evidence_artifact_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_artifact
    ADD CONSTRAINT evidence_artifact_pkey PRIMARY KEY (artifact_id);


--
-- Name: evidence_instance evidence_instance_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_pkey PRIMARY KEY (instance_id);


--
-- Name: sim_in_device excl_sim_in_device; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT excl_sim_in_device EXCLUDE USING gist (sim_id WITH =, valid_time WITH &&);


--
-- Name: sim_number_assignment excl_sim_number_assignment; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT excl_sim_number_assignment EXCLUDE USING gist (phone_number_id WITH =, valid_time WITH &&);


--
-- Name: extraction extraction_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_pkey PRIMARY KEY (extraction_id);


--
-- Name: financial_account financial_account_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.financial_account
    ADD CONSTRAINT financial_account_pkey PRIMARY KEY (entity_id);


--
-- Name: fir fir_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_pkey PRIMARY KEY (fir_id);


--
-- Name: forensic_report forensic_report_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.forensic_report
    ADD CONSTRAINT forensic_report_pkey PRIMARY KEY (report_id);


--
-- Name: generation_run generation_run_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.generation_run
    ADD CONSTRAINT generation_run_pkey PRIMARY KEY (generation_run_id);


--
-- Name: hypothesis hypothesis_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_pkey PRIMARY KEY (hypothesis_id);


--
-- Name: hypothesis_support hypothesis_support_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_pkey PRIMARY KEY (support_id);


--
-- Name: identity_candidate identity_candidate_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_pkey PRIMARY KEY (candidate_id);


--
-- Name: identity_merge_event identity_merge_event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_pkey PRIMARY KEY (merge_event_id);


--
-- Name: identity_resolution identity_resolution_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_pkey PRIMARY KEY (resolution_id);


--
-- Name: identity_split_event identity_split_event_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_pkey PRIMARY KEY (split_event_id);


--
-- Name: investigation_task investigation_task_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_pkey PRIMARY KEY (task_id);


--
-- Name: investigative_case investigative_case_case_number_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_case_number_key UNIQUE (case_number);


--
-- Name: investigative_case investigative_case_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_pkey PRIMARY KEY (case_id);


--
-- Name: investigative_lead investigative_lead_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_pkey PRIMARY KEY (lead_id);


--
-- Name: legal_restriction legal_restriction_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_pkey PRIMARY KEY (restriction_id);


--
-- Name: location location_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_pkey PRIMARY KEY (entity_id);


--
-- Name: medical_report medical_report_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.medical_report
    ADD CONSTRAINT medical_report_pkey PRIMARY KEY (report_id);


--
-- Name: network network_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.network
    ADD CONSTRAINT network_pkey PRIMARY KEY (entity_id);


--
-- Name: observation observation_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_pkey PRIMARY KEY (observation_id);


--
-- Name: organization organization_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (entity_id);


--
-- Name: outbox outbox_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.outbox
    ADD CONSTRAINT outbox_pkey PRIMARY KEY (id);


--
-- Name: person_alias person_alias_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT person_alias_pkey PRIMARY KEY (alias_id);


--
-- Name: person person_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person
    ADD CONSTRAINT person_pkey PRIMARY KEY (entity_id);


--
-- Name: phone_number phone_number_msisdn_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_msisdn_key UNIQUE (msisdn);


--
-- Name: phone_number phone_number_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_pkey PRIMARY KEY (entity_id);


--
-- Name: property property_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.property
    ADD CONSTRAINT property_pkey PRIMARY KEY (entity_id);


--
-- Name: provenance provenance_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.provenance
    ADD CONSTRAINT provenance_pkey PRIMARY KEY (provenance_id);


--
-- Name: scenario scenario_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.scenario
    ADD CONSTRAINT scenario_pkey PRIMARY KEY (scenario_id);


--
-- Name: sim sim_iccid_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_iccid_key UNIQUE (iccid);


--
-- Name: sim sim_imsi_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_imsi_key UNIQUE (imsi);


--
-- Name: sim_in_device sim_in_device_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_pkey PRIMARY KEY (id);


--
-- Name: sim_number_assignment sim_number_assignment_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_pkey PRIMARY KEY (assignment_id);


--
-- Name: sim sim_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_pkey PRIMARY KEY (entity_id);


--
-- Name: source_identity source_identity_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_pkey PRIMARY KEY (entity_id);


--
-- Name: source source_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source
    ADD CONSTRAINT source_pkey PRIMARY KEY (source_id);


--
-- Name: source_record source_record_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_pkey PRIMARY KEY (source_record_id);


--
-- Name: source source_source_name_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source
    ADD CONSTRAINT source_source_name_key UNIQUE (source_name);


--
-- Name: case_access uq_case_access; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT uq_case_access UNIQUE (case_id, user_id);


--
-- Name: case_entity_role uq_case_entity_role; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT uq_case_entity_role UNIQUE (case_id, entity_id, role);


--
-- Name: entity uq_entity_id_type; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT uq_entity_id_type UNIQUE (entity_id, entity_type);


--
-- Name: event_participant uq_event_participant; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT uq_event_participant UNIQUE (event_id, entity_id, participant_role);


--
-- Name: evidence_artifact uq_evidence_artifact_hash; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_artifact
    ADD CONSTRAINT uq_evidence_artifact_hash UNIQUE (sha256_hash, hash_algorithm);


--
-- Name: hypothesis_support uq_hypothesis_support; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT uq_hypothesis_support UNIQUE (hypothesis_id, assertion_id);


--
-- Name: identity_candidate uq_identity_candidate; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT uq_identity_candidate UNIQUE (source_identity_id, proposed_person_id);


--
-- Name: person_alias uq_person_alias; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT uq_person_alias UNIQUE (person_id, alias_value, alias_type);


--
-- Name: vehicle vehicle_pkey; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_pkey PRIMARY KEY (entity_id);


--
-- Name: vehicle vehicle_registration_number_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_registration_number_key UNIQUE (registration_number);


--
-- Name: vehicle vehicle_vin_key; Type: CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_vin_key UNIQUE (vin);


--
-- Name: audit_event block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.audit_event FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: evidence_artifact block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.evidence_artifact FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: identity_merge_event block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.identity_merge_event FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: identity_resolution block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.identity_resolution FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: identity_split_event block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.identity_split_event FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: legal_restriction block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.legal_restriction FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: provenance block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.provenance FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: source_record block_mutation_trigger; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER block_mutation_trigger BEFORE DELETE OR UPDATE ON civix.source_record FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();


--
-- Name: account_holder enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.account_holder FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: assertion enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.assertion FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: case_entity_role enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.case_entity_role FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: case_link enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.case_link FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: device enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.device FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: event enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.event FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: event_participant enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.event_participant FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: extraction enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.extraction FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: financial_account enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.financial_account FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: fir enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.fir FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: forensic_report enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.forensic_report FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: hypothesis enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.hypothesis FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: hypothesis_support enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.hypothesis_support FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: investigation_task enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.investigation_task FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: investigative_lead enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.investigative_lead FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: location enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.location FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: medical_report enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.medical_report FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: network enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.network FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: observation enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.observation FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: organization enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.organization FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: person enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.person FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: phone_number enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.phone_number FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: property enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.property FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: sim enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.sim FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: sim_in_device enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.sim_in_device FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: sim_number_assignment enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.sim_number_assignment FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: vehicle enforce_no_delete_unless_synthetic; Type: TRIGGER; Schema: civix; Owner: postgres
--

CREATE TRIGGER enforce_no_delete_unless_synthetic BEFORE DELETE ON civix.vehicle FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();


--
-- Name: account_holder account_holder_account_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_account_id_fkey FOREIGN KEY (account_id) REFERENCES civix.financial_account(entity_id);


--
-- Name: account_holder account_holder_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: account_holder account_holder_holder_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_holder_entity_id_fkey FOREIGN KEY (holder_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: account_holder account_holder_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.account_holder
    ADD CONSTRAINT account_holder_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: analysis_run analysis_run_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.analysis_run
    ADD CONSTRAINT analysis_run_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: analysis_run analysis_run_initiated_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.analysis_run
    ADD CONSTRAINT analysis_run_initiated_by_fkey FOREIGN KEY (initiated_by) REFERENCES civix.civix_user(user_id);


--
-- Name: assertion assertion_asserted_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_asserted_by_fkey FOREIGN KEY (asserted_by) REFERENCES civix.civix_user(user_id);


--
-- Name: assertion assertion_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: assertion assertion_object_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_object_entity_id_fkey FOREIGN KEY (object_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: assertion assertion_object_location_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_object_location_id_fkey FOREIGN KEY (object_location_id) REFERENCES civix.location(entity_id);


--
-- Name: assertion assertion_source_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_source_analysis_run_id_fkey FOREIGN KEY (source_analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: assertion assertion_subject_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.assertion
    ADD CONSTRAINT assertion_subject_entity_id_fkey FOREIGN KEY (subject_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: audit_event audit_event_case_context_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.audit_event
    ADD CONSTRAINT audit_event_case_context_id_fkey FOREIGN KEY (case_context_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: audit_event audit_event_user_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.audit_event
    ADD CONSTRAINT audit_event_user_id_fkey FOREIGN KEY (user_id) REFERENCES civix.civix_user(user_id);


--
-- Name: case_access case_access_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: case_access case_access_granted_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_granted_by_fkey FOREIGN KEY (granted_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_access case_access_revoked_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_revoked_by_fkey FOREIGN KEY (revoked_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_access case_access_user_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_access
    ADD CONSTRAINT case_access_user_id_fkey FOREIGN KEY (user_id) REFERENCES civix.civix_user(user_id);


--
-- Name: case_entity_role case_entity_role_assigned_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_entity_role case_entity_role_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: case_entity_role case_entity_role_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: case_entity_role case_entity_role_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_entity_role
    ADD CONSTRAINT case_entity_role_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: case_link case_link_authorized_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_authorized_by_fkey FOREIGN KEY (authorized_by) REFERENCES civix.civix_user(user_id);


--
-- Name: case_link case_link_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: case_link case_link_source_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_source_case_id_fkey FOREIGN KEY (source_case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: case_link case_link_target_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.case_link
    ADD CONSTRAINT case_link_target_case_id_fkey FOREIGN KEY (target_case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: data_quality_issue data_quality_issue_detection_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.data_quality_issue
    ADD CONSTRAINT data_quality_issue_detection_run_id_fkey FOREIGN KEY (detection_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: data_quality_issue data_quality_issue_resolved_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.data_quality_issue
    ADD CONSTRAINT data_quality_issue_resolved_by_fkey FOREIGN KEY (resolved_by) REFERENCES civix.civix_user(user_id);


--
-- Name: device device_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: device device_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.device
    ADD CONSTRAINT device_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: entity entity_created_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT entity_created_by_fkey FOREIGN KEY (created_by) REFERENCES civix.civix_user(user_id);


--
-- Name: entity entity_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.entity
    ADD CONSTRAINT entity_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: event event_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event
    ADD CONSTRAINT event_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: event_participant event_participant_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_entity_id_fkey FOREIGN KEY (entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: event_participant event_participant_event_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_event_id_fkey FOREIGN KEY (event_id) REFERENCES civix.event(event_id);


--
-- Name: event_participant event_participant_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event_participant
    ADD CONSTRAINT event_participant_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: event event_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.event
    ADD CONSTRAINT event_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: evidence_instance evidence_instance_acquired_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_acquired_by_fkey FOREIGN KEY (acquired_by) REFERENCES civix.civix_user(user_id);


--
-- Name: evidence_instance evidence_instance_artifact_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_artifact_id_fkey FOREIGN KEY (artifact_id) REFERENCES civix.evidence_artifact(artifact_id);


--
-- Name: evidence_instance evidence_instance_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: evidence_instance evidence_instance_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: evidence_instance evidence_instance_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.evidence_instance
    ADD CONSTRAINT evidence_instance_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: extraction extraction_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: extraction extraction_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: extraction extraction_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: extraction extraction_superseded_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.extraction
    ADD CONSTRAINT extraction_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES civix.extraction(extraction_id);


--
-- Name: financial_account financial_account_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.financial_account
    ADD CONSTRAINT financial_account_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: financial_account financial_account_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.financial_account
    ADD CONSTRAINT financial_account_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: fir fir_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: fir fir_complainant_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_complainant_entity_id_fkey FOREIGN KEY (complainant_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: fir fir_filed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_filed_by_fkey FOREIGN KEY (filed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: fir fir_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: fir fir_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.fir
    ADD CONSTRAINT fir_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: forensic_report forensic_report_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.forensic_report
    ADD CONSTRAINT forensic_report_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: forensic_report forensic_report_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.forensic_report
    ADD CONSTRAINT forensic_report_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: generation_run generation_run_dataset_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.generation_run
    ADD CONSTRAINT generation_run_dataset_id_fkey FOREIGN KEY (dataset_id) REFERENCES civix.dataset(dataset_id);


--
-- Name: generation_run generation_run_scenario_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.generation_run
    ADD CONSTRAINT generation_run_scenario_id_fkey FOREIGN KEY (scenario_id) REFERENCES civix.scenario(scenario_id);


--
-- Name: hypothesis hypothesis_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: hypothesis hypothesis_confirmed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_confirmed_by_fkey FOREIGN KEY (confirmed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: hypothesis hypothesis_created_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_created_by_fkey FOREIGN KEY (created_by) REFERENCES civix.civix_user(user_id);


--
-- Name: hypothesis hypothesis_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis
    ADD CONSTRAINT hypothesis_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: hypothesis_support hypothesis_support_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: hypothesis_support hypothesis_support_assertion_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_assertion_id_fkey FOREIGN KEY (assertion_id) REFERENCES civix.assertion(assertion_id);


--
-- Name: hypothesis_support hypothesis_support_assigned_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_assigned_by_fkey FOREIGN KEY (assigned_by) REFERENCES civix.civix_user(user_id);


--
-- Name: hypothesis_support hypothesis_support_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: hypothesis_support hypothesis_support_hypothesis_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.hypothesis_support
    ADD CONSTRAINT hypothesis_support_hypothesis_id_fkey FOREIGN KEY (hypothesis_id) REFERENCES civix.hypothesis(hypothesis_id);


--
-- Name: identity_candidate identity_candidate_analysis_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_analysis_run_id_fkey FOREIGN KEY (analysis_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: identity_candidate identity_candidate_proposed_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_proposed_person_id_fkey FOREIGN KEY (proposed_person_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_candidate identity_candidate_source_identity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_candidate
    ADD CONSTRAINT identity_candidate_source_identity_id_fkey FOREIGN KEY (source_identity_id) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_merge_event identity_merge_event_decided_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES civix.civix_user(user_id);


--
-- Name: identity_merge_event identity_merge_event_merged_into_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_merged_into_person_id_fkey FOREIGN KEY (merged_into_person_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_merge_event identity_merge_event_resolution_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_resolution_id_fkey FOREIGN KEY (resolution_id) REFERENCES civix.identity_resolution(resolution_id);


--
-- Name: identity_merge_event identity_merge_event_source_identity_a_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_source_identity_a_fkey FOREIGN KEY (source_identity_a) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_merge_event identity_merge_event_source_identity_b_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_merge_event
    ADD CONSTRAINT identity_merge_event_source_identity_b_fkey FOREIGN KEY (source_identity_b) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_resolution identity_resolution_candidate_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_candidate_id_fkey FOREIGN KEY (candidate_id) REFERENCES civix.identity_candidate(candidate_id);


--
-- Name: identity_resolution identity_resolution_decided_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES civix.civix_user(user_id);


--
-- Name: identity_resolution identity_resolution_resolved_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_resolved_person_id_fkey FOREIGN KEY (resolved_person_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_resolution identity_resolution_source_identity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_source_identity_id_fkey FOREIGN KEY (source_identity_id) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_resolution identity_resolution_superseded_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_resolution
    ADD CONSTRAINT identity_resolution_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES civix.identity_resolution(resolution_id);


--
-- Name: identity_split_event identity_split_event_decided_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_decided_by_fkey FOREIGN KEY (decided_by) REFERENCES civix.civix_user(user_id);


--
-- Name: identity_split_event identity_split_event_new_person_b_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_new_person_b_id_fkey FOREIGN KEY (new_person_b_id) REFERENCES civix.person(entity_id);


--
-- Name: identity_split_event identity_split_event_original_resolution_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_original_resolution_id_fkey FOREIGN KEY (original_resolution_id) REFERENCES civix.identity_resolution(resolution_id);


--
-- Name: identity_split_event identity_split_event_split_source_identity_a_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_split_source_identity_a_fkey FOREIGN KEY (split_source_identity_a) REFERENCES civix.source_identity(entity_id);


--
-- Name: identity_split_event identity_split_event_split_source_identity_b_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.identity_split_event
    ADD CONSTRAINT identity_split_event_split_source_identity_b_fkey FOREIGN KEY (split_source_identity_b) REFERENCES civix.source_identity(entity_id);


--
-- Name: investigation_task investigation_task_assigned_to_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES civix.civix_user(user_id);


--
-- Name: investigation_task investigation_task_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: investigation_task investigation_task_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: investigation_task investigation_task_lead_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigation_task
    ADD CONSTRAINT investigation_task_lead_id_fkey FOREIGN KEY (lead_id) REFERENCES civix.investigative_lead(lead_id);


--
-- Name: investigative_case investigative_case_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: investigative_case investigative_case_lead_investigator_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_case
    ADD CONSTRAINT investigative_case_lead_investigator_id_fkey FOREIGN KEY (lead_investigator_id) REFERENCES civix.civix_user(user_id);


--
-- Name: investigative_lead investigative_lead_case_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_case_id_fkey FOREIGN KEY (case_id) REFERENCES civix.investigative_case(case_id);


--
-- Name: investigative_lead investigative_lead_disposed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_disposed_by_fkey FOREIGN KEY (disposed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: investigative_lead investigative_lead_generated_by_person_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_generated_by_person_fkey FOREIGN KEY (generated_by_person) REFERENCES civix.civix_user(user_id);


--
-- Name: investigative_lead investigative_lead_generated_by_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_generated_by_run_id_fkey FOREIGN KEY (generated_by_run_id) REFERENCES civix.analysis_run(run_id);


--
-- Name: investigative_lead investigative_lead_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.investigative_lead
    ADD CONSTRAINT investigative_lead_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: legal_restriction legal_restriction_created_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_created_by_fkey FOREIGN KEY (created_by) REFERENCES civix.civix_user(user_id);


--
-- Name: legal_restriction legal_restriction_lifted_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_lifted_by_fkey FOREIGN KEY (lifted_by) REFERENCES civix.civix_user(user_id);


--
-- Name: legal_restriction legal_restriction_target_artifact_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_target_artifact_id_fkey FOREIGN KEY (target_artifact_id) REFERENCES civix.evidence_artifact(artifact_id);


--
-- Name: legal_restriction legal_restriction_target_entity_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.legal_restriction
    ADD CONSTRAINT legal_restriction_target_entity_id_fkey FOREIGN KEY (target_entity_id) REFERENCES civix.entity(entity_id);


--
-- Name: location location_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: location location_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: location location_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.location
    ADD CONSTRAINT location_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: medical_report medical_report_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.medical_report
    ADD CONSTRAINT medical_report_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: medical_report medical_report_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.medical_report
    ADD CONSTRAINT medical_report_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: network network_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.network
    ADD CONSTRAINT network_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: network network_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.network
    ADD CONSTRAINT network_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: observation observation_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: observation observation_instance_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_instance_id_fkey FOREIGN KEY (instance_id) REFERENCES civix.evidence_instance(instance_id);


--
-- Name: observation observation_observed_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.observation
    ADD CONSTRAINT observation_observed_by_fkey FOREIGN KEY (observed_by) REFERENCES civix.civix_user(user_id);


--
-- Name: organization organization_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.organization
    ADD CONSTRAINT organization_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: organization organization_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.organization
    ADD CONSTRAINT organization_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: person_alias person_alias_person_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT person_alias_person_id_fkey FOREIGN KEY (person_id) REFERENCES civix.person(entity_id);


--
-- Name: person_alias person_alias_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person_alias
    ADD CONSTRAINT person_alias_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: person person_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person
    ADD CONSTRAINT person_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: person person_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.person
    ADD CONSTRAINT person_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: phone_number phone_number_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: phone_number phone_number_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.phone_number
    ADD CONSTRAINT phone_number_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: property property_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.property
    ADD CONSTRAINT property_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: property property_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.property
    ADD CONSTRAINT property_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim sim_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: sim sim_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim
    ADD CONSTRAINT sim_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim_in_device sim_in_device_device_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_device_id_fkey FOREIGN KEY (device_id) REFERENCES civix.device(entity_id);


--
-- Name: sim_in_device sim_in_device_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim_in_device sim_in_device_sim_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_in_device
    ADD CONSTRAINT sim_in_device_sim_id_fkey FOREIGN KEY (sim_id) REFERENCES civix.sim(entity_id);


--
-- Name: sim_number_assignment sim_number_assignment_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: sim_number_assignment sim_number_assignment_phone_number_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_phone_number_id_fkey FOREIGN KEY (phone_number_id) REFERENCES civix.phone_number(entity_id);


--
-- Name: sim_number_assignment sim_number_assignment_sim_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_sim_id_fkey FOREIGN KEY (sim_id) REFERENCES civix.sim(entity_id);


--
-- Name: sim_number_assignment sim_number_assignment_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.sim_number_assignment
    ADD CONSTRAINT sim_number_assignment_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: source_identity source_identity_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: source_identity source_identity_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: source_identity source_identity_source_record_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_identity
    ADD CONSTRAINT source_identity_source_record_id_fkey FOREIGN KEY (source_record_id) REFERENCES civix.source_record(source_record_id);


--
-- Name: source_record source_record_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: source_record source_record_source_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_source_id_fkey FOREIGN KEY (source_id) REFERENCES civix.source(source_id);


--
-- Name: source_record source_record_superseded_by_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source_record
    ADD CONSTRAINT source_record_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES civix.source_record(source_record_id);


--
-- Name: source source_source_handler_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.source
    ADD CONSTRAINT source_source_handler_id_fkey FOREIGN KEY (source_handler_id) REFERENCES civix.civix_user(user_id);


--
-- Name: vehicle vehicle_entity_id_entity_type_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_entity_id_entity_type_fkey FOREIGN KEY (entity_id, entity_type) REFERENCES civix.entity(entity_id, entity_type);


--
-- Name: vehicle vehicle_generation_run_id_fkey; Type: FK CONSTRAINT; Schema: civix; Owner: postgres
--

ALTER TABLE ONLY civix.vehicle
    ADD CONSTRAINT vehicle_generation_run_id_fkey FOREIGN KEY (generation_run_id) REFERENCES civix.generation_run(generation_run_id);


--
-- Name: case_entity_role; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.case_entity_role ENABLE ROW LEVEL SECURITY;

--
-- Name: case_entity_role case_entity_role_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY case_entity_role_access_policy ON civix.case_entity_role USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_entity_role.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_entity_role.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: case_link; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.case_link ENABLE ROW LEVEL SECURITY;

--
-- Name: case_link case_link_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY case_link_access_policy ON civix.case_link USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_link.source_case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = case_link.source_case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: evidence_instance; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.evidence_instance ENABLE ROW LEVEL SECURITY;

--
-- Name: evidence_instance evidence_instance_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY evidence_instance_access_policy ON civix.evidence_instance USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = evidence_instance.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = evidence_instance.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: extraction; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.extraction ENABLE ROW LEVEL SECURITY;

--
-- Name: extraction extraction_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY extraction_access_policy ON civix.extraction USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = extraction.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = extraction.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: fir; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.fir ENABLE ROW LEVEL SECURITY;

--
-- Name: fir fir_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY fir_access_policy ON civix.fir USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = fir.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = fir.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: forensic_report; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.forensic_report ENABLE ROW LEVEL SECURITY;

--
-- Name: forensic_report forensic_report_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY forensic_report_access_policy ON civix.forensic_report USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = forensic_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = forensic_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: hypothesis; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.hypothesis ENABLE ROW LEVEL SECURITY;

--
-- Name: hypothesis hypothesis_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY hypothesis_access_policy ON civix.hypothesis USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = hypothesis.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = hypothesis.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: hypothesis_support; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.hypothesis_support ENABLE ROW LEVEL SECURITY;

--
-- Name: hypothesis_support hypothesis_support_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY hypothesis_support_access_policy ON civix.hypothesis_support USING ((EXISTS ( SELECT 1
   FROM (civix.hypothesis h
     JOIN civix.case_access ca ON ((h.case_id = ca.case_id)))
  WHERE ((h.hypothesis_id = hypothesis_support.hypothesis_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.hypothesis h
     JOIN civix.case_access ca ON ((h.case_id = ca.case_id)))
  WHERE ((h.hypothesis_id = hypothesis_support.hypothesis_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: investigation_task; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.investigation_task ENABLE ROW LEVEL SECURITY;

--
-- Name: investigation_task investigation_task_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY investigation_task_access_policy ON civix.investigation_task USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigation_task.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigation_task.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: investigative_case; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.investigative_case ENABLE ROW LEVEL SECURITY;

--
-- Name: investigative_case investigative_case_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY investigative_case_access_policy ON civix.investigative_case USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_case.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_case.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: investigative_lead; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.investigative_lead ENABLE ROW LEVEL SECURITY;

--
-- Name: investigative_lead investigative_lead_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY investigative_lead_access_policy ON civix.investigative_lead USING ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_lead.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM civix.case_access
  WHERE ((case_access.case_id = investigative_lead.case_id) AND (case_access.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (case_access.is_revoked = false)))));


--
-- Name: medical_report; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.medical_report ENABLE ROW LEVEL SECURITY;

--
-- Name: medical_report medical_report_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY medical_report_access_policy ON civix.medical_report USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = medical_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = medical_report.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- Name: observation; Type: ROW SECURITY; Schema: civix; Owner: postgres
--

ALTER TABLE civix.observation ENABLE ROW LEVEL SECURITY;

--
-- Name: observation observation_access_policy; Type: POLICY; Schema: civix; Owner: postgres
--

CREATE POLICY observation_access_policy ON civix.observation USING ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = observation.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false))))) WITH CHECK ((EXISTS ( SELECT 1
   FROM (civix.evidence_instance e
     JOIN civix.case_access ca ON ((e.case_id = ca.case_id)))
  WHERE ((e.instance_id = observation.instance_id) AND (ca.user_id = (current_setting('civix.current_user_id'::text, true))::uuid) AND (ca.is_revoked = false)))));


--
-- PostgreSQL database dump complete
--

\unrestrict fC4jAHZeroKohFvgYkAKaDGcDPddjcxSWPZ32vjTLH1QxA7k2KREx4LLuqpTazF

