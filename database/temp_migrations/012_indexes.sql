-- =============================================================================
-- CIVIX Platform — Migration 012: Indexes
-- Phase 2A Physical DDL Implementation
-- Date: 2026-08-29
-- Authority: docs/phase2/PHASE2A_ARCHITECTURE_READINESS_CHECK.md §Required Indexes
--            docs/03_DATABASE_SCHEMA_BIBLE.md §Architecture Invariants
-- =============================================================================
-- INDEX PHILOSOPHY:
--   Every index here has a documented purpose.
--   Speculative/redundant indexes are NOT created.
--   Large-scale partitioning indexes (>10M rows) are deferred to Phase 2B.
-- =============================================================================

SET search_path TO civix, public;

-- ---------------------------------------------------------------------------
-- ENTITY INDEXES
-- ---------------------------------------------------------------------------

-- Core entity dispatch: finding all entities of a type (subtype queries)
CREATE INDEX idx_entity_type
    ON civix.entity (entity_type);

-- Entity lifecycle: filtering tombstoned/restricted entities from views
CREATE INDEX idx_entity_visibility
    ON civix.entity (visibility_status)
    WHERE visibility_status != 'ACTIVE';

-- ---------------------------------------------------------------------------
-- SOURCE & EVIDENCE INDEXES
-- ---------------------------------------------------------------------------

-- Source record lookup by source system
CREATE INDEX idx_source_record_source
    ON civix.source_record (source_id);

-- Source record by external reference (CDR-000002, etc.)
CREATE INDEX idx_source_record_external_ref
    ON civix.source_record (external_reference)
    WHERE external_reference IS NOT NULL;

-- Synthetic filtering: exclude synthetic rows from production queries
CREATE INDEX idx_source_record_generation_run
    ON civix.source_record (generation_run_id)
    WHERE generation_run_id IS NOT NULL;

-- Evidence deduplication lookup: exact hash match
-- NOTE: sha256_hash is BYTEA — standard btree works correctly
CREATE INDEX idx_artifact_hash
    ON civix.evidence_artifact (sha256_hash, hash_algorithm);

-- Artifact parent chain: finding all derivatives of an original
CREATE INDEX idx_artifact_parent
    ON civix.evidence_artifact (parent_artifact_id)
    WHERE parent_artifact_id IS NOT NULL;

-- Evidence instance by case (primary RLS lookup)
CREATE INDEX idx_evidence_instance_case
    ON civix.evidence_instance (case_id);

-- Evidence instance by artifact (GC reachability check)
CREATE INDEX idx_evidence_instance_artifact
    ON civix.evidence_instance (artifact_id);

-- Evidence instance transaction time (AS-OF queries)
CREATE INDEX idx_evidence_instance_tx
    ON civix.evidence_instance (tx_start, tx_end);

-- ---------------------------------------------------------------------------
-- IDENTITY INDEXES
-- ---------------------------------------------------------------------------

-- Source identity lookup by raw_identifier + type (de-duplication on ingest)
CREATE INDEX idx_source_identity_lookup
    ON civix.source_identity (raw_identifier, identifier_type);

-- Source identity transaction time
CREATE INDEX idx_source_identity_tx
    ON civix.source_identity (tx_start);

-- Identity candidate: find candidates for a given source identity
CREATE INDEX idx_identity_candidate_si
    ON civix.identity_candidate (source_identity_id);

-- Identity candidate: find all identities proposed to a person
CREATE INDEX idx_identity_candidate_person
    ON civix.identity_candidate (proposed_person_id);

-- Identity resolution: active resolutions only
CREATE INDEX idx_identity_resolution_active
    ON civix.identity_resolution (source_identity_id)
    WHERE tx_end IS NULL;

-- ---------------------------------------------------------------------------
-- TELECOM INDEXES
-- ---------------------------------------------------------------------------

-- SIM number assignment: look up current MSISDN from phone_number_id
CREATE INDEX idx_sim_number_phone
    ON civix.sim_number_assignment (phone_number_id);

-- SIM number assignment: look up by SIM
CREATE INDEX idx_sim_number_sim
    ON civix.sim_number_assignment (sim_id);

-- SIM in device: look up by device
CREATE INDEX idx_sim_in_device_device
    ON civix.sim_in_device (device_id);

-- Person device use: find all devices a person has used
CREATE INDEX idx_person_device_use_person
    ON civix.person_device_use (person_id);

-- Person device use: find all users of a device
CREATE INDEX idx_person_device_use_device
    ON civix.person_device_use (device_id);

-- Person SIM ownership: by person
CREATE INDEX idx_person_sim_person
    ON civix.person_sim_ownership (person_id);

-- ---------------------------------------------------------------------------
-- FINANCIAL INDEXES
-- ---------------------------------------------------------------------------

-- Account holder: find all role-holders for an account
CREATE INDEX idx_account_holder_account
    ON civix.account_holder (account_id);

-- Account holder: find all accounts linked to an entity
CREATE INDEX idx_account_holder_entity
    ON civix.account_holder (holder_entity_id);

-- Account holder: active roles only (tx_end IS NULL)
CREATE INDEX idx_account_holder_active
    ON civix.account_holder (account_id, holder_entity_id)
    WHERE tx_end IS NULL;

-- ---------------------------------------------------------------------------
-- CASE MANAGEMENT INDEXES
-- ---------------------------------------------------------------------------

-- Case access: primary RLS lookup (user → cases they can access)
CREATE INDEX idx_case_access_user
    ON civix.case_access (user_id)
    WHERE is_revoked = FALSE;

-- Case access: all grants for a case (admin view)
CREATE INDEX idx_case_access_case
    ON civix.case_access (case_id);

-- Case entity role: all active roles in a case
CREATE INDEX idx_case_entity_role_active
    ON civix.case_entity_role (case_id)
    WHERE tx_end IS NULL;

-- Case entity role: all roles for an entity across cases
CREATE INDEX idx_case_entity_role_entity
    ON civix.case_entity_role (entity_id);

-- Case link: cross-case discovery
CREATE INDEX idx_case_link_source
    ON civix.case_link (source_case_id);

CREATE INDEX idx_case_link_target
    ON civix.case_link (target_case_id);

-- ---------------------------------------------------------------------------
-- EPISTEMIC PIPELINE INDEXES
-- ---------------------------------------------------------------------------

-- Observation: by evidence instance (provenance join)
CREATE INDEX idx_observation_instance
    ON civix.observation (instance_id);

-- Extraction: by evidence instance
CREATE INDEX idx_extraction_instance
    ON civix.extraction (instance_id);

-- Extraction: active only (not superseded)
CREATE INDEX idx_extraction_active
    ON civix.extraction (instance_id)
    WHERE is_superseded = FALSE;

-- Extraction: by analysis run (model output review)
CREATE INDEX idx_extraction_run
    ON civix.extraction (analysis_run_id);

-- Event: by type (classification queries)
CREATE INDEX idx_event_type
    ON civix.event (event_type);

-- Event: by transaction time (AS-OF reconstruction)
CREATE INDEX idx_event_tx
    ON civix.event (tx_start);

-- Event: by source record (ingestion tracing)
CREATE INDEX idx_event_source_record
    ON civix.event (source_record_id)
    WHERE source_record_id IS NOT NULL;

-- Event: synthetic filtering
CREATE INDEX idx_event_generation_run
    ON civix.event (generation_run_id)
    WHERE generation_run_id IS NOT NULL;

-- Event participant: all participants in an event (N-ary lookup)
CREATE INDEX idx_event_participant_event
    ON civix.event_participant (event_id);

-- Event participant: all events involving an entity (entity history)
CREATE INDEX idx_event_participant_entity
    ON civix.event_participant (entity_id);

-- Event participant: by role (find all drivers, victims, etc.)
CREATE INDEX idx_event_participant_role
    ON civix.event_participant (participant_role);

-- Assertion: subject entity (outgoing assertion lookup)
CREATE INDEX idx_assertion_subject
    ON civix.assertion (subject_entity_id);

-- Assertion: object entity (incoming assertion lookup)
CREATE INDEX idx_assertion_object
    ON civix.assertion (object_entity_id)
    WHERE object_entity_id IS NOT NULL;

-- Assertion: predicate filtering
CREATE INDEX idx_assertion_predicate
    ON civix.assertion (predicate);

-- Assertion: transaction time (AS-OF bitemporal queries)
CREATE INDEX idx_assertion_tx
    ON civix.assertion (tx_start, tx_end);

-- *** CRITICAL — BLK-15/ADR-017 ***
-- Assertion authorized_case_ids: GIN index for array overlap operator (&&)
-- This is the primary RLS performance optimization.
-- Without this, RLS on authorized_case_ids would require a sequential scan.
CREATE INDEX idx_assertion_authorized_cases
    ON civix.assertion USING GIN (authorized_case_ids);

-- Assertion: active only (tx_end IS NULL)
CREATE INDEX idx_assertion_active
    ON civix.assertion (subject_entity_id)
    WHERE tx_end IS NULL;

-- Assertion: synthetic filtering
CREATE INDEX idx_assertion_generation_run
    ON civix.assertion (generation_run_id)
    WHERE generation_run_id IS NOT NULL;

-- Hypothesis: by case
CREATE INDEX idx_hypothesis_case
    ON civix.hypothesis (case_id);

-- Hypothesis: active only
CREATE INDEX idx_hypothesis_active
    ON civix.hypothesis (case_id)
    WHERE tx_end IS NULL AND status = 'ACTIVE';

-- Hypothesis support: by hypothesis (evidence evaluation)
CREATE INDEX idx_hyp_support_hypothesis
    ON civix.hypothesis_support (hypothesis_id);

-- Hypothesis support: by assertion (reverse lookup)
CREATE INDEX idx_hyp_support_assertion
    ON civix.hypothesis_support (assertion_id);

-- Hypothesis support: active only
CREATE INDEX idx_hyp_support_active
    ON civix.hypothesis_support (hypothesis_id)
    WHERE tx_end IS NULL;

-- Hypothesis support: AS-OF queries
CREATE INDEX idx_hyp_support_tx
    ON civix.hypothesis_support (tx_start);

-- ---------------------------------------------------------------------------
-- WORKFLOW INDEXES
-- ---------------------------------------------------------------------------

-- Lead: by case
CREATE INDEX idx_lead_case
    ON civix.investigative_lead (case_id);

-- Lead: by status (priority queue view)
CREATE INDEX idx_lead_status
    ON civix.investigative_lead (status, priority);

-- Task: by case
CREATE INDEX idx_task_case
    ON civix.investigation_task (case_id);

-- Task: by assignee
CREATE INDEX idx_task_assignee
    ON civix.investigation_task (assigned_to)
    WHERE assigned_to IS NOT NULL;

-- ---------------------------------------------------------------------------
-- PROVENANCE & DATA QUALITY INDEXES
-- ---------------------------------------------------------------------------

-- Provenance: find all derivations from a source (downstream taint)
CREATE INDEX idx_provenance_source
    ON civix.provenance (source_type, source_id);

-- Provenance: find all sources of a derived entity (upstream tracing)
CREATE INDEX idx_provenance_derived
    ON civix.provenance (derived_type, derived_id);

-- Data quality: by affected entity (quick taint check)
CREATE INDEX idx_dq_entity
    ON civix.data_quality_issue (affected_entity_type, affected_entity_id);

-- Data quality: open issues only
CREATE INDEX idx_dq_open
    ON civix.data_quality_issue (severity, detected_at)
    WHERE status = 'OPEN';

-- ---------------------------------------------------------------------------
-- LEGAL & AUDIT INDEXES
-- ---------------------------------------------------------------------------

-- Legal restriction: by entity
CREATE INDEX idx_legal_restriction_entity
    ON civix.legal_restriction (target_entity_id)
    WHERE target_entity_id IS NOT NULL;

-- Audit event: by user (audit trail review)
CREATE INDEX idx_audit_user
    ON civix.audit_event (user_id, timestamp);

-- Audit event: by target (who touched this record?)
CREATE INDEX idx_audit_target
    ON civix.audit_event (target_table, target_id);

-- ---------------------------------------------------------------------------
-- OUTBOX INDEX
-- ---------------------------------------------------------------------------

-- Outbox: pending events (CDC consumer's primary query)
-- Partial index: only unconsumed events need fast lookup
CREATE INDEX idx_outbox_pending
    ON civix.outbox (created_at)
    WHERE consumed_at IS NULL;

-- ---------------------------------------------------------------------------
-- SPATIAL INDEX (PostGIS)
-- ---------------------------------------------------------------------------

-- Location geometry: spatial queries (PostGIS GIST index)
CREATE INDEX idx_location_geometry
    ON civix.location USING GIN (geometry);

-- Property boundary: spatial queries
CREATE INDEX idx_property_geometry
    ON civix.property USING GIN (boundary_geometry)
    WHERE boundary_geometry IS NOT NULL;
