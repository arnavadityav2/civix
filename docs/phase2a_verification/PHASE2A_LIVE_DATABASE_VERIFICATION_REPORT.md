# CIVIX — PHASE 2A LIVE DATABASE VERIFICATION REPORT
**Generated**: 2026-08-28 22:59:56 UTC  
**Database**: civix_verify @ localhost:5432  
**Architecture**: FROZEN — no modifications made  

---

## 1. EXECUTIVE VERDICT

### ✅ PHASE 2A LIVE DATABASE VERIFICATION = **PASS**

All 109 tests passed. The physical PostgreSQL schema faithfully implements the frozen CIVIX architecture.

| Metric | Value |
|---|---|
| Total Tests | 109 |
| PASS | 109 |
| FAIL | 0 |
| Verdict | PASS |

---

## 2. ENVIRONMENT

- **psql_binary**: C:\Program Files\PostgreSQL\17\bin\psql.exe
- **psql_version**: psql (PostgreSQL) 17.11
- **postgres_connection**: OK
- **server_version**: PostgreSQL 17.11 on x86_64-windows, compiled by msvc-19.44.35228, 64-bit
- **postgis_version**: NOT_INSTALLED_YET (will be installed by migration 000)
- **ext_pgcrypto**: AVAILABLE
- **ext_btree_gist**: AVAILABLE
- **ext_uuid-ossp**: AVAILABLE
- **discovery_timestamp**: 2026-08-28T22:59:41.424109+00:00

---

## 3. MIGRATION RESULTS

| Migration | Status |
|---|---|
| 000_extensions.sql | PASS: 1.39s |
| 001_enums.sql | PASS: 0.10s |
| 002_users_and_synthetic.sql | PASS: 0.17s |
| 003_source_and_evidence.sql | PASS: 0.19s |
| 004_core_entities.sql | PASS: 0.15s |
| 005_identity_resolution.sql | PASS: 0.12s |
| 006_telecom_and_financial.sql | PASS: 0.20s |
| 007_cases_and_access.sql | PASS: 0.09s |
| 008_epistemic_pipeline.sql | PASS: 0.29s |
| 009_workflow_and_legal.sql | PASS: 0.11s |
| 010_provenance_and_quality.sql | PASS: 0.07s |
| 011_triggers.sql | PASS: 0.06s |
| 012_indexes.sql | PASS: 0.26s |
| 013_rls.sql | PASS: 0.13s |
| 014_validation.sql | PASS: 0.12s |

---

## Section: TABLES

- ✅ **schema_civix_exists**: PASS
**found_tables**: ["account_holder", "analysis_run", "assertion", "audit_event", "case_access", "case_entity_role", "case_link", "civix_user", "data_quality_issue", "dataset", "device", "entity", "event", "event_participant", "evidence_artifact", "evidence_instance", "extraction", "financial_account", "fir", "forensic_report", "generation_run", "hypothesis", "hypothesis_support", "identity_candidate", "identity_merge_event", "identity_resolution", "identity_split_event", "investigation_task", "investigative_case", "investigative_lead", "legal_restriction", "location", "medical_report", "network", "observation", "organization", "outbox", "person", "person_alias", "person_device_use", "person_sim_ownership", "phone_number", "property", "provenance", "scenario", "sim", "sim_in_device", "sim_number_assignment", "source", "source_identity", "source_record", "vehicle"]

- **found_count**: 52
- ✅ **all_required_tables_present**: PASS: 51 tables verified
**unexpected_tables**: ["entity"]


---

## Section: ENUMS

**found_enums**: ["audit_action_enum", "case_entity_role_enum", "case_permission_enum", "case_priority_enum", "case_status_enum", "case_type_enum", "civix_role_enum", "clearance_enum", "data_quality_issue_type_enum", "dataset_type_enum", "entity_type_enum", "epistemic_status_enum", "event_type_enum", "extraction_type_enum", "hash_algorithm_enum", "hypothesis_status_enum", "identity_resolution_status_enum", "lead_priority_enum", "lead_status_enum", "legal_restriction_type_enum", "location_type_enum", "participant_role_enum", "predicate_enum", "source_identity_type_enum", "support_stance_enum", "task_status_enum", "task_type_enum"]

- **found_count**: 27
- ✅ **enum_count**: PASS: 27 ENUMs found
- ✅ **hypothesis_status_enum**: PASS: 5 values verified
- ✅ **lead_status_enum**: PASS: 6 values verified
- ✅ **support_stance_enum**: PASS: 4 values verified

---

## Section: CONSTRAINTS

- ✅ **person_no_is_criminal**: PASS: INV-17 enforced
- ✅ **assertion_no_stance**: PASS: INV-01 enforced
- ✅ **source_identity_no_extraction_id**: PASS: ADR-014 enforced
- ✅ **entity_has_visibility_status**: PASS: BLK-16 enforced
- ✅ **event_no_entity_fks**: PASS: ADR-021/INV-05 enforced
- ✅ **uq_artifact_hash**: PASS: ADR-004
- ✅ **excl_sim_number_time**: PASS: ADR-009 GIST exclusion
- ✅ **excl_sim_in_device_time**: PASS: INV-15 GIST exclusion
- ✅ **uq_event_participant**: PASS: BLK-21
- ✅ **uq_active_hypothesis_support**: PASS: Partial index — BLK-06
- ✅ **uq_active_case_entity_role**: PASS: Partial index — BLK-12
- ✅ **uq_active_case_access**: PASS: Partial index — Gate 3
- ✅ **chk_hypothesis_human_confirmation**: PASS: INV-08
- ✅ **chk_assertion_has_object**: PASS: assertion object required
- ✅ **chk_case_closed_after_opened**: PASS: date sanity
- ✅ **ext_postgis**: PASS: extension installed
- ✅ **ext_uuid-ossp**: PASS: extension installed
- ✅ **ext_pgcrypto**: PASS: extension installed
- ✅ **ext_btree_gist**: PASS: extension installed

---

## Section: TRIGGERS


---

## Section: BITEMPORAL

- ✅ **test_user_created**: PASS
- ✅ **test_case_created**: PASS
- ✅ **hypothesis_insert**: PASS
- ✅ **assertion_insert**: PASS
- ✅ **hypothesis_support_insert**: PASS
- ✅ **hypothesis_support_bitemporal_trigger**: PASS: UPDATE created 2 rows (1 closed, 1 active) — BLK-17 ✓
- ✅ **audit_event_insert**: PASS
- ✅ **audit_event_immutable**: PASS: UPDATE correctly rejected — INV-13 ✓
- ✅ **as_of_reconstruction**: PASS: AS-OF query returns exactly 1 active row

---

## Section: IDENTITY

- ✅ **entity_delete_blocked**: PASS: Physical DELETE rejected — BLK-16/ADR-018 ✓
- ✅ **entity_tombstone_works**: PASS: visibility_status = TOMBSTONED accepted
- ✅ **tombstone_outbox_emitted**: PASS: TOMBSTONE_NODE emitted to outbox — BLK-18 ✓
- ✅ **source_record_immutable**: PASS: UPDATE on source_record rejected ✓

---

## Section: H4_EVENT

- ✅ **property_mutation_event_created**: PASS: event_id=a8f58d33-ac05-45fb-a7b2-dddded294371
- ✅ **two_target_properties_on_one_event**: PASS: PROP-01 and PROP-08 both attached with TARGET_PROPERTY role ✓
- ✅ **event_appears_once**: PASS: One event, two participants ✓
- ✅ **unique_event_entity_role**: PASS: Duplicate (event, entity, role) correctly rejected ✓
- ✅ **multi_role_same_entity**: PASS: Same entity with REGISTERED_OWNER + DRIVER roles ✓

---

## Section: EVIDENCE

- ✅ **artifact_insert**: PASS
- ✅ **artifact_dedup**: PASS: Duplicate (hash, algorithm) correctly rejected — ADR-004 ✓
- ✅ **artifact_different_algo_allowed**: PASS: Same hash value, different algorithm → new row ✓
- ✅ **artifact_parent_chain**: PASS: Child artifact with parent_artifact_id ✓
- ✅ **parent_artifact_restrict**: PASS: Parent deletion with active child correctly rejected — BLK-22/ADR-022 ✓

---

## Section: RLS

- ✅ **rls_enabled_investigative_case**: PASS
- ✅ **rls_enabled_evidence_instance**: PASS
- ✅ **rls_enabled_assertion**: PASS
- ✅ **rls_enabled_hypothesis**: PASS
- ✅ **rls_enabled_hypothesis_support**: PASS
- ✅ **rls_enabled_investigative_lead**: PASS
- ✅ **rls_enabled_investigation_task**: PASS
- ✅ **rls_enabled_case_entity_role**: PASS
- ✅ **rls_enabled_fir**: PASS
- ✅ **policy_assertion**: PASS: Policy 'policy_assertion_select' exists ✓
- ✅ **policy_investigative_case**: PASS: Policy 'policy_case_access' exists ✓
- ✅ **policy_evidence_instance**: PASS: Policy 'policy_evidence_instance_select' exists ✓
- ✅ **fn_get_accessible_case_ids**: PASS: RLS helper function exists
- ✅ **fn_current_user_is_admin**: PASS: RLS helper function exists
- ✅ **fn_append_case_to_assertion**: PASS: RLS helper function exists
- ✅ **fn_revoke_case_from_assertion**: PASS: RLS helper function exists

---

## Section: OUTBOX

- ✅ **tombstone_node_in_outbox**: PASS: 1 TOMBSTONE_NODE records ✓
- ✅ **outbox_col_id**: PASS
- ✅ **outbox_col_entity_id**: PASS
- ✅ **outbox_col_action**: PASS
- ✅ **outbox_col_entity_type**: PASS
- ✅ **outbox_col_payload**: PASS
- ✅ **outbox_col_created_at**: PASS
- ✅ **outbox_col_consumed_at**: PASS
- ✅ **pending_query**: PASS: 4 pending CDC events

---

## Section: INDEXES

- ✅ **idx_assertion_authorized_cases**: PASS
- ✅ **idx_assertion_subject**: PASS
- ✅ **idx_assertion_predicate**: PASS
- ✅ **idx_assertion_tx**: PASS
- ✅ **idx_assertion_active**: PASS
- ✅ **idx_evidence_instance_case**: PASS
- ✅ **idx_evidence_instance_artifact**: PASS
- ✅ **idx_event_participant_event**: PASS
- ✅ **idx_event_participant_entity**: PASS
- ✅ **idx_hypothesis_case**: PASS
- ✅ **idx_hyp_support_hypothesis**: PASS
- ✅ **idx_hyp_support_active**: PASS
- ✅ **idx_case_access_user**: PASS
- ✅ **idx_outbox_pending**: PASS
- ✅ **idx_location_geometry**: PASS
- ✅ **idx_entity_type**: PASS
- ✅ **idx_entity_visibility**: PASS
- ✅ **idx_provenance_derived**: PASS
- ✅ **idx_provenance_source**: PASS
- ⊘ **total_indexes**: 141

---

## Section: VALIDATION_SQL

- **returncode**: 0
- ⊘ **stdout**: SET
  extname   | extversion 
------------+------------
 btree_gist | 1.7
 pgcrypto   | 1.3
 postgis    | 3.6.2
 uuid-ossp  | 1.1
(4 rows)

 nspname 
---------
 civix
(1 row)

             typname             
---------------------------------
 audit_action_enum
 case_entity_role_enum
 case_permission_enum
 case_priority_enum
 case_status_enum
 case_type_enum
 civix_role_enum
 clearance_enum
 data_quality_issue_type_enum
 dataset_type_enum
 entity_type_enum
 epistemic_status_enum
 event_type_enum
 extraction_type_enum
 hash_algorithm_enum
 hypothesis_status_enum
 identity_resolution_status_enum
 lead_priority_enum
 lead_status_enum
 legal_restriction_type_enum
 location_type_enum
 participant_role_enum
 predicate_enum
 source_identity_type_enum
 support_stance_enum
 task_status_enum
 task_type_enum
(27 rows)

  enumlabel   
--------------
 ACTIVE
 UNDER_REVIEW
 CONFIRMED
 REFUTED
 ARCHIVED
(5 rows)

   enumlabel    
----------------
 OPEN
 IN_PROGRESS
 CONFIRMED
 FALSE_POSITIVE
 CLOSED
 DEFERRED
(6 rows)

 predicate_count 
-----------------
              35
(1 row)

       tablename       
-----------------------
 account_holder
 analysis_run
 assertion
 audit_event
 case_access
 case_entity_role
 case_link
 civix_user
 data_quality_issue
 dataset
 device
 entity
 event
 event_participant
 evidence_artifact
 evidence_instance
 extraction
 financial_account
 fir
 forensic_report
 generation_run
 hypothesis
 hypothesis_support
 identity_candidate
 identity_merge_event
 identity_resolution
 identity_split_event
 investigation_task
 investigative_case
 investigative_lead
 legal_restriction
 location
 medical_report
 network
 observation
 organization
 outbox
 person
 person_alias
 person_device_use
 person_sim_ownership
 phone_number
 property
 provenance
 scenario
 sim
 sim_in_device
 sim_number_assignment
 source
 source_identity
 source_record
 vehicle
(52 rows)

     conname      | contype 
------------------+---------
 uq_artifact_hash | u
(1 row)

        tgname        
----------------------
 trg_entity_no_delete
(1 row)

              conname              
-----------------------------------
 chk_hypothesis_human_confirmation
(1 row)

          indexname           
------------------------------
 uq_active_hypothesis_support
(1 row)

       indexname       
-----------------------
 uq_active_case_access
(1 row)

           indexname            |                                            indexdef                                            
--------------------------------+------------------------------------------------------------------------------------------------
 idx_assertion_authorized_cases | CREATE INDEX idx_assertion_authorized_cases ON civix.assertion USING gin (authorized_case_ids)
(1 row)

       conname        | contype 
----------------------+---------
 excl_sim_number_time | x
(1 row)

         conname         
-------------------------
 excl_sim_in_device_time
(1 row)

       conname        
----------------------
 uq_event_p
- ⊘ **stderr**: 
- ✅ **014_validation_executed**: PASS: All validation queries executed without error

---

## FILES INSPECTED (NOT MODIFIED)

- `database/migrations/000_extensions.sql`
- `database/migrations/001_enums.sql`
- `database/migrations/002_users_and_synthetic.sql`
- `database/migrations/003_source_and_evidence.sql`
- `database/migrations/004_core_entities.sql`
- `database/migrations/005_identity_resolution.sql`
- `database/migrations/006_telecom_and_financial.sql`
- `database/migrations/007_cases_and_access.sql`
- `database/migrations/008_epistemic_pipeline.sql`
- `database/migrations/009_workflow_and_legal.sql`
- `database/migrations/010_provenance_and_quality.sql`
- `database/migrations/011_triggers.sql`
- `database/migrations/012_indexes.sql`
- `database/migrations/013_rls.sql`
- `database/migrations/014_validation.sql`
- `database/verify_phase2a.py` (this script)

**Files modified**: NONE (verification only)

---

## NEXT STEPS

Phase 2B — Scalable Synthetic Data Engine is now ready for explicit authorization.
