"""workflow_forensics

Revision ID: 008
Revises: 007
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, TIMESTAMP

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. civix.investigative_lead
    op.create_table(
        'investigative_lead',
        sa.Column('lead_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('generated_by_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.analysis_run.run_id'), nullable=True),
        sa.Column('generated_by_person', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('lead_text', sa.Text(), nullable=False),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('priority', ENUM(name='lead_priority_enum', schema='civix', create_type=False), nullable=False, server_default='MEDIUM'),
        sa.Column('status', ENUM(name='lead_status_enum', schema='civix', create_type=False), nullable=False, server_default='OPEN'),
        sa.Column('ai_confidence', sa.Numeric(5, 4), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('disposition_notes', sa.Text(), nullable=True),
        sa.Column('disposed_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('disposed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    op.create_check_constraint('chk_lead_generator', 'investigative_lead', 'generated_by_run_id IS NOT NULL OR generated_by_person IS NOT NULL', schema='civix')

    # 2. civix.investigation_task
    op.create_table(
        'investigation_task',
        sa.Column('task_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('lead_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_lead.lead_id'), nullable=True),
        sa.Column('case_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=False),
        sa.Column('task_type', ENUM(name='task_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('assigned_to', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('status', ENUM(name='task_status_enum', schema='civix', create_type=False), nullable=False, server_default='PENDING'),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

    # 3. civix.forensic_report
    op.create_table(
        'forensic_report',
        sa.Column('report_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('instance_id', UUID(as_uuid=True), sa.ForeignKey('civix.evidence_instance.instance_id'), nullable=False),
        sa.Column('report_type', sa.Text(), nullable=False),
        sa.Column('lab_name', sa.Text(), nullable=True),
        sa.Column('examiner_name', sa.Text(), nullable=True),
        sa.Column('findings_summary', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

    # 4. civix.medical_report
    op.create_table(
        'medical_report',
        sa.Column('report_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('instance_id', UUID(as_uuid=True), sa.ForeignKey('civix.evidence_instance.instance_id'), nullable=False),
        sa.Column('examination_type', sa.Text(), nullable=False),
        sa.Column('findings_summary', sa.Text(), nullable=True),
        sa.Column('practitioner_name', sa.Text(), nullable=True),
        sa.Column('examination_date', sa.Date(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

def downgrade() -> None:
    pass
