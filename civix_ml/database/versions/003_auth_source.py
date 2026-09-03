"""auth_source

Revision ID: 003
Revises: 002
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, TIMESTAMP, BYTEA

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. (Removed Role Creation)
    # Role provisioning and secret injection is delegated to deployment bootstrap scripts/environment management.

    # 2. civix.civix_user
    op.create_table(
        'civix_user',
        sa.Column('user_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('external_auth_id', sa.Text(), nullable=False, unique=True),
        sa.Column('username', sa.Text(), nullable=False, unique=True),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('role', ENUM(name='civix_role_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('clearance_level', ENUM(name='clearance_enum', schema='civix', create_type=False), nullable=False, server_default='UNCLASSIFIED'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('department', sa.Text(), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login_at', TIMESTAMP(timezone=True), nullable=True),
        schema='civix'
    )

    # 3. civix.source
    op.create_table(
        'source',
        sa.Column('source_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_name', sa.Text(), nullable=False, unique=True),
        sa.Column('agency_type', sa.Text(), nullable=False),
        sa.Column('reliability_score', sa.Numeric(3, 2), nullable=True),
        sa.Column('jurisdiction', sa.Text(), nullable=True),
        sa.Column('is_identity_protected', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('source_handler_id', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='civix'
    )
    
    # Check constraint for reliability score
    op.create_check_constraint(
        'check_reliability_score',
        'source',
        'reliability_score >= 0.0 AND reliability_score <= 1.0',
        schema='civix'
    )

    # Note: generation_run will be created here to allow source_record to reference it.
    # Synthetic Data Control (Metadata Only)
    op.create_table(
        'dataset',
        sa.Column('dataset_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('dataset_type', ENUM(name='dataset_type_enum', schema='civix', create_type=False), nullable=False),
        schema='civix'
    )
    
    op.create_table(
        'scenario',
        sa.Column('scenario_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('config_metadata', sa.JSON(), nullable=True),
        schema='civix'
    )

    op.create_table(
        'generation_run',
        sa.Column('generation_run_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('dataset_id', UUID(as_uuid=True), sa.ForeignKey('civix.dataset.dataset_id'), nullable=False),
        sa.Column('scenario_id', UUID(as_uuid=True), sa.ForeignKey('civix.scenario.scenario_id'), nullable=False),
        sa.Column('run_timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('world_seed', sa.BigInteger(), nullable=True),
        sa.Column('generator_version', sa.Text(), nullable=True),
        schema='civix'
    )

    # 4. civix.source_record
    op.create_table(
        'source_record',
        sa.Column('source_record_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('civix.source.source_id'), nullable=False),
        sa.Column('external_reference', sa.Text(), nullable=True),
        sa.Column('record_type', sa.Text(), nullable=False),
        sa.Column('raw_content_hash', BYTEA(), nullable=True),
        sa.Column('received_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('superseded_by', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        schema='civix'
    )

    # 5. civix.evidence_artifact
    op.create_table(
        'evidence_artifact',
        sa.Column('artifact_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('sha256_hash', BYTEA(), nullable=False),
        sa.Column('hash_algorithm', ENUM(name='hash_algorithm_enum', schema='civix', create_type=False), nullable=False, server_default='SHA256'),
        sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
        sa.Column('mime_type', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.Text(), nullable=True),
        sa.Column('storage_uri', sa.Text(), nullable=True),
        sa.Column('is_integrity_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('acquired_at', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='civix'
    )

    op.create_unique_constraint('uq_evidence_artifact_hash', 'evidence_artifact', ['sha256_hash', 'hash_algorithm'], schema='civix')

def downgrade() -> None:
    pass
