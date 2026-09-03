"""epistemic

Revision ID: 007
Revises: 006
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, TIMESTAMP, TSTZRANGE, JSONB

# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. civix.analysis_run
    op.create_table(
        'analysis_run',
        sa.Column('run_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('model_version', sa.Text(), nullable=False),
        sa.Column('algorithm_type', sa.Text(), nullable=False),
        sa.Column('algorithm_parameters', JSONB(), nullable=True),
        sa.Column('input_snapshot_hash', sa.LargeBinary(), nullable=True),
        sa.Column('input_snapshot_tx_time', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('started_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('finished_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('initiated_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    # Missing Identity Tables from Migration 05 that require analysis_run
    # civix.person_alias
    op.create_table(
        'person_alias',
        sa.Column('alias_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('person_id', UUID(as_uuid=True), sa.ForeignKey('civix.person.entity_id'), nullable=False),
        sa.Column('alias_value', sa.Text(), nullable=False),
        sa.Column('alias_type', sa.Text(), nullable=False),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='civix'
    )
    op.create_unique_constraint('uq_person_alias', 'person_alias', ['person_id', 'alias_value', 'alias_type'], schema='civix')

    # civix.identity_candidate
    op.create_table(
        'identity_candidate',
        sa.Column('candidate_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_identity_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_identity.entity_id'), nullable=False),
        sa.Column('proposed_person_id', UUID(as_uuid=True), sa.ForeignKey('civix.person.entity_id'), nullable=False),
        sa.Column('ai_confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('analysis_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.analysis_run.run_id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='civix'
    )
    op.create_unique_constraint('uq_identity_candidate', 'identity_candidate', ['source_identity_id', 'proposed_person_id'], schema='civix')
    op.create_check_constraint('chk_ai_confidence', 'identity_candidate', 'ai_confidence >= 0 AND ai_confidence <= 1', schema='civix')

    # civix.identity_resolution
    op.create_table(
        'identity_resolution',
        sa.Column('resolution_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_identity_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_identity.entity_id'), nullable=False),
        sa.Column('candidate_id', UUID(as_uuid=True), sa.ForeignKey('civix.identity_candidate.candidate_id'), nullable=True),
        sa.Column('resolved_person_id', UUID(as_uuid=True), sa.ForeignKey('civix.person.entity_id'), nullable=True),
        sa.Column('status', ENUM(name='identity_resolution_status_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('decided_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('decision_notes', sa.Text(), nullable=True),
        sa.Column('superseded_by', UUID(as_uuid=True), sa.ForeignKey('civix.identity_resolution.resolution_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tx_end', TIMESTAMP(timezone=True), nullable=True),
        schema='civix'
    )
    op.create_check_constraint('chk_identity_resolution_status', 'identity_resolution', "status != 'ACCEPTED' OR resolved_person_id IS NOT NULL", schema='civix')

    # civix.identity_merge_event
    op.create_table(
        'identity_merge_event',
        sa.Column('merge_event_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_identity_a', UUID(as_uuid=True), sa.ForeignKey('civix.source_identity.entity_id'), nullable=False),
        sa.Column('source_identity_b', UUID(as_uuid=True), sa.ForeignKey('civix.source_identity.entity_id'), nullable=False),
        sa.Column('merged_into_person_id', UUID(as_uuid=True), sa.ForeignKey('civix.person.entity_id'), nullable=False),
        sa.Column('resolution_id', UUID(as_uuid=True), sa.ForeignKey('civix.identity_resolution.resolution_id'), nullable=False),
        sa.Column('decided_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('occurred_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('reason', sa.Text(), nullable=True),
        schema='civix'
    )

    # civix.identity_split_event
    op.create_table(
        'identity_split_event',
        sa.Column('split_event_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('original_resolution_id', UUID(as_uuid=True), sa.ForeignKey('civix.identity_resolution.resolution_id'), nullable=False),
        sa.Column('split_source_identity_a', UUID(as_uuid=True), sa.ForeignKey('civix.source_identity.entity_id'), nullable=False),
        sa.Column('split_source_identity_b', UUID(as_uuid=True), sa.ForeignKey('civix.source_identity.entity_id'), nullable=False),
        sa.Column('new_person_b_id', UUID(as_uuid=True), sa.ForeignKey('civix.person.entity_id'), nullable=False),
        sa.Column('decided_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('occurred_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='civix'
    )

    # 2. civix.observation
    op.create_table(
        'observation',
        sa.Column('observation_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('instance_id', UUID(as_uuid=True), sa.ForeignKey('civix.evidence_instance.instance_id'), nullable=False),
        sa.Column('observer_type', sa.Text(), nullable=False),
        sa.Column('observed_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('observation_type', sa.Text(), nullable=True),
        sa.Column('observation_text', sa.Text(), nullable=True),
        sa.Column('structured_content', JSONB(), nullable=True),
        sa.Column('observed_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

    # 3. civix.extraction
    op.create_table(
        'extraction',
        sa.Column('extraction_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('instance_id', UUID(as_uuid=True), sa.ForeignKey('civix.evidence_instance.instance_id'), nullable=False),
        sa.Column('analysis_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.analysis_run.run_id'), nullable=False),
        sa.Column('extraction_type', ENUM(name='extraction_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('extracted_value', JSONB(), nullable=False),
        sa.Column('ai_confidence', sa.Numeric(5, 4), nullable=False),
        sa.Column('is_superseded', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('superseded_by', UUID(as_uuid=True), sa.ForeignKey('civix.extraction.extraction_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    op.create_check_constraint('chk_ai_confidence_ext', 'extraction', 'ai_confidence >= 0 AND ai_confidence <= 1', schema='civix')

    # 4. civix.event
    op.create_table(
        'event',
        sa.Column('event_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_type', ENUM(name='event_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('occurred_at', TSTZRANGE(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

    # 5. civix.event_participant
    op.create_table(
        'event_participant',
        sa.Column('participant_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_id', UUID(as_uuid=True), sa.ForeignKey('civix.event.event_id'), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=False),
        sa.Column('participant_role', ENUM(name='participant_role_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('role_confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    op.create_unique_constraint('uq_event_participant', 'event_participant', ['event_id', 'entity_id', 'participant_role'], schema='civix')

    # 6. civix.assertion
    op.create_table(
        'assertion',
        sa.Column('assertion_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('subject_entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=False),
        sa.Column('predicate', ENUM(name='predicate_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('object_entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=True),
        sa.Column('object_value', sa.Text(), nullable=True),
        sa.Column('object_location_id', UUID(as_uuid=True), sa.ForeignKey('civix.location.entity_id'), nullable=True),
        sa.Column('epistemic_status', ENUM(name='epistemic_status_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('ai_confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('asserted_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('source_analysis_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.analysis_run.run_id'), nullable=True),
        sa.Column('valid_from', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('valid_to', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tx_end', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    op.create_check_constraint('chk_assertion_object', 'assertion', 'object_entity_id IS NOT NULL OR object_value IS NOT NULL OR object_location_id IS NOT NULL', schema='civix')
    op.create_check_constraint('chk_assertion_source', 'assertion', 'asserted_by IS NOT NULL OR source_analysis_run_id IS NOT NULL', schema='civix')
    op.create_check_constraint('chk_assertion_confidence', 'assertion', 'ai_confidence IS NULL OR (ai_confidence >= 0 AND ai_confidence <= 1)', schema='civix')

    # 7. civix.hypothesis
    op.create_table(
        'hypothesis',
        sa.Column('hypothesis_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('hypothesis_text', sa.Text(), nullable=False),
        sa.Column('status', ENUM(name='hypothesis_status_enum', schema='civix', create_type=False), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('confirmed_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tx_end', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    op.create_check_constraint('chk_hypothesis_status', 'hypothesis', "status != 'CONFIRMED' OR confirmed_by IS NOT NULL", schema='civix')

    # 8. civix.hypothesis_support
    op.create_table(
        'hypothesis_support',
        sa.Column('support_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('hypothesis_id', UUID(as_uuid=True), sa.ForeignKey('civix.hypothesis.hypothesis_id'), nullable=False),
        sa.Column('assertion_id', UUID(as_uuid=True), sa.ForeignKey('civix.assertion.assertion_id'), nullable=False),
        sa.Column('stance', ENUM(name='support_stance_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('weight', sa.Numeric(5, 4), nullable=False, server_default='1.0'),
        sa.Column('assigned_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('analysis_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.analysis_run.run_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    op.create_unique_constraint('uq_hypothesis_support', 'hypothesis_support', ['hypothesis_id', 'assertion_id'], schema='civix')

def downgrade() -> None:
    pass
