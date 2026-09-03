"""relationships

Revision ID: 005
Revises: 004
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP, TSTZRANGE

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. civix.sim_number_assignment
    op.create_table(
        'sim_number_assignment',
        sa.Column('assignment_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('sim_id', UUID(as_uuid=True), sa.ForeignKey('civix.sim.entity_id'), nullable=False),
        sa.Column('phone_number_id', UUID(as_uuid=True), sa.ForeignKey('civix.phone_number.entity_id'), nullable=False),
        sa.Column('valid_time', TSTZRANGE(), nullable=False),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    # EXCLUDE USING GIST
    op.execute("""
        ALTER TABLE civix.sim_number_assignment
        ADD CONSTRAINT excl_sim_number_assignment
        EXCLUDE USING GIST (phone_number_id WITH =, valid_time WITH &&);
    """)
    
    # 2. civix.sim_in_device
    op.create_table(
        'sim_in_device',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('sim_id', UUID(as_uuid=True), sa.ForeignKey('civix.sim.entity_id'), nullable=False),
        sa.Column('device_id', UUID(as_uuid=True), sa.ForeignKey('civix.device.entity_id'), nullable=False),
        sa.Column('valid_time', TSTZRANGE(), nullable=False),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    # EXCLUDE USING GIST
    op.execute("""
        ALTER TABLE civix.sim_in_device
        ADD CONSTRAINT excl_sim_in_device
        EXCLUDE USING GIST (sim_id WITH =, valid_time WITH &&);
    """)
    
    # 3. civix.account_holder
    op.create_table(
        'account_holder',
        sa.Column('holder_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('civix.financial_account.entity_id'), nullable=False),
        sa.Column('holder_entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=False),
        sa.Column('holder_role', sa.Text(), nullable=False),
        sa.Column('ownership_percentage', sa.Numeric(5, 2), nullable=True),
        sa.Column('valid_time', TSTZRANGE(), nullable=False),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )
    
    op.create_check_constraint(
        'check_ownership_percentage',
        'account_holder',
        'ownership_percentage >= 0 AND ownership_percentage <= 100',
        schema='civix'
    )

def downgrade() -> None:
    pass
