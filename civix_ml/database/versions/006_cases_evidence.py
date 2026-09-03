"""cases_evidence

Revision ID: 006
Revises: 005
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, TIMESTAMP, ARRAY

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. civix.investigative_case
    op.create_table(
        'investigative_case',
        sa.Column('case_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('case_number', sa.Text(), nullable=False, unique=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('case_type', ENUM(name='case_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('status', ENUM(name='case_status_enum', schema='civix', create_type=False), nullable=False, server_default='OPEN'),
        sa.Column('priority', ENUM(name='case_priority_enum', schema='civix', create_type=False), nullable=False, server_default='MEDIUM'),
        sa.Column('jurisdiction', sa.Text(), nullable=False),
        sa.Column('investigating_unit', sa.Text(), nullable=True),
        sa.Column('opened_at', sa.Date(), nullable=False),
        sa.Column('closed_at', sa.Date(), nullable=True),
        sa.Column('lead_investigator_id', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    op.create_check_constraint('chk_case_closed_date', 'investigative_case', 'closed_at IS NULL OR closed_at >= opened_at', schema='civix')

    # 2. civix.case_access
    op.create_table(
        'case_access',
        sa.Column('access_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('permission_level', ENUM(name='case_permission_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('granted_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('granted_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('valid_until', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('revoked_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('revoked_at', TIMESTAMP(timezone=True), nullable=True),
        schema='civix'
    )
    
    op.create_unique_constraint('uq_case_access', 'case_access', ['case_id', 'user_id'], schema='civix')

    # 3. civix.case_entity_role
    op.create_table(
        'case_entity_role',
        sa.Column('role_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=False),
        sa.Column('role', ENUM(name='case_entity_role_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('role_basis', sa.Text(), nullable=True),
        sa.Column('assigned_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('valid_from', sa.Date(), nullable=True),
        sa.Column('valid_to', sa.Date(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    op.create_unique_constraint('uq_case_entity_role', 'case_entity_role', ['case_id', 'entity_id', 'role'], schema='civix')

    # 4. civix.fir
    op.create_table(
        'fir',
        sa.Column('fir_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('fir_number', sa.Text(), nullable=False),
        sa.Column('police_station', sa.Text(), nullable=False),
        sa.Column('district', sa.Text(), nullable=False),
        sa.Column('filed_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('filed_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('complainant_entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=True),
        sa.Column('sections_invoked', ARRAY(sa.Text()), nullable=True),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

    # 5. civix.case_link
    op.create_table(
        'case_link',
        sa.Column('link_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('target_case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('linked_object_type', sa.Text(), nullable=False),
        sa.Column('linked_object_id', UUID(as_uuid=True), nullable=False),
        sa.Column('share_scope', sa.Text(), nullable=False),
        sa.Column('authorized_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    op.create_check_constraint('chk_case_link_not_self', 'case_link', 'source_case_id != target_case_id', schema='civix')

    # 6. civix.evidence_instance
    op.create_table(
        'evidence_instance',
        sa.Column('instance_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('artifact_id', UUID(as_uuid=True), sa.ForeignKey('civix.evidence_artifact.artifact_id'), nullable=False),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('acquired_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('acquisition_method', sa.Text(), nullable=True),
        sa.Column('acquisition_context', sa.Text(), nullable=True),
        sa.Column('legal_status', sa.Text(), nullable=False, server_default='ACTIVE'),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tx_end', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

def downgrade() -> None:
    pass
