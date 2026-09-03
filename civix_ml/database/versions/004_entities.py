"""entities

Revision ID: 004
Revises: 003
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, TIMESTAMP

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. civix.entity - Universal Supertype
    op.create_table(
        'entity',
        sa.Column('entity_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        schema='civix'
    )
    
    # Subtype Integrity: UNIQUE constraint on (entity_id, entity_type)
    op.create_unique_constraint('uq_entity_id_type', 'entity', ['entity_id', 'entity_type'], schema='civix')

    # Subtype definitions
    
    # civix.source_identity
    op.create_table(
        'source_identity',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='SOURCE_IDENTITY'),
        sa.Column('raw_identifier', sa.Text(), nullable=False),
        sa.Column('identifier_type', ENUM(name='source_identity_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('observed_at', TIMESTAMP(timezone=True), nullable=False),
        sa.Column('tx_start', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('tx_end', TIMESTAMP(timezone=True), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'SOURCE_IDENTITY'", name='chk_entity_type_source_identity'),
        schema='civix'
    )

    # civix.person
    op.create_table(
        'person',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='PERSON'),
        sa.Column('display_name', sa.Text(), nullable=False),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('gender', sa.Text(), nullable=True),
        sa.Column('nationality', sa.String(3), nullable=True),
        sa.Column('is_deceased', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deceased_at', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'PERSON'", name='chk_entity_type_person'),
        schema='civix'
    )
    
    # civix.phone_number
    op.create_table(
        'phone_number',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='PHONE_NUMBER'),
        sa.Column('msisdn', sa.String(15), nullable=False, unique=True),
        sa.Column('country_code', sa.String(3), nullable=True, server_default='IND'),
        sa.Column('operator', sa.Text(), nullable=True),
        sa.Column('number_type', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'PHONE_NUMBER'", name='chk_entity_type_phone_number'),
        schema='civix'
    )
    
    # civix.sim
    op.create_table(
        'sim',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='SIM'),
        sa.Column('iccid', sa.String(22), nullable=False, unique=True),
        sa.Column('imsi', sa.String(15), nullable=True, unique=True),
        sa.Column('issuing_operator', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'SIM'", name='chk_entity_type_sim'),
        schema='civix'
    )
    
    # civix.device
    op.create_table(
        'device',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='DEVICE'),
        sa.Column('imei', sa.String(17), nullable=True, unique=True),
        sa.Column('mac_address', sa.String(17), nullable=True, unique=True),
        sa.Column('device_type', sa.Text(), nullable=False),
        sa.Column('manufacturer', sa.Text(), nullable=True),
        sa.Column('model', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'DEVICE'", name='chk_entity_type_device'),
        schema='civix'
    )
    
    # civix.vehicle
    op.create_table(
        'vehicle',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='VEHICLE'),
        sa.Column('registration_number', sa.Text(), nullable=False, unique=True),
        sa.Column('vin', sa.Text(), nullable=True, unique=True),
        sa.Column('make', sa.Text(), nullable=True),
        sa.Column('model', sa.Text(), nullable=True),
        sa.Column('color', sa.Text(), nullable=True),
        sa.Column('vehicle_type', sa.Text(), nullable=False),
        sa.Column('registration_year', sa.Integer(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'VEHICLE'", name='chk_entity_type_vehicle'),
        schema='civix'
    )
    
    # civix.property
    op.create_table(
        'property',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='PROPERTY'),
        sa.Column('property_ref', sa.Text(), nullable=False),
        sa.Column('property_type', sa.Text(), nullable=False),
        sa.Column('area_sqm', sa.Numeric(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'PROPERTY'", name='chk_entity_type_property'),
        schema='civix'
    )
    
    # Adding PostGIS Geometry separately since Alembic core might stumble on it without GeoAlchemy2
    op.execute("ALTER TABLE civix.property ADD COLUMN boundary_geometry GEOMETRY(Polygon, 4326) NULL;")
    
    # civix.financial_account
    op.create_table(
        'financial_account',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='FINANCIAL_ACCOUNT'),
        sa.Column('masked_number', sa.Text(), nullable=False),
        sa.Column('account_type', sa.Text(), nullable=False),
        sa.Column('bank_name', sa.Text(), nullable=True),
        sa.Column('ifsc_code', sa.String(11), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True, server_default='INR'),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'FINANCIAL_ACCOUNT'", name='chk_entity_type_financial_account'),
        schema='civix'
    )
    
    # civix.organization
    op.create_table(
        'organization',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='ORGANIZATION'),
        sa.Column('legal_name', sa.Text(), nullable=False),
        sa.Column('org_type', sa.Text(), nullable=False),
        sa.Column('registration_number', sa.Text(), nullable=True),
        sa.Column('incorporation_date', sa.Date(), nullable=True),
        sa.Column('jurisdiction', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'ORGANIZATION'", name='chk_entity_type_organization'),
        schema='civix'
    )
    
    # civix.network
    op.create_table(
        'network',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='NETWORK'),
        sa.Column('network_name', sa.Text(), nullable=False),
        sa.Column('network_type', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'NETWORK'", name='chk_entity_type_network'),
        schema='civix'
    )
    
    # civix.location
    op.create_table(
        'location',
        sa.Column('entity_id', UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_type', ENUM(name='entity_type_enum', schema='civix', create_type=False), nullable=False, server_default='LOCATION'),
        sa.Column('location_name', sa.Text(), nullable=True),
        sa.Column('location_type', ENUM(name='location_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('uncertainty_radius_meters', sa.Float(), nullable=True),
        sa.Column('altitude_meters', sa.Float(), nullable=True),
        sa.Column('azimuth_degrees', sa.Float(), nullable=True),
        sa.Column('beamwidth_degrees', sa.Float(), nullable=True),
        sa.Column('source_record_id', UUID(as_uuid=True), sa.ForeignKey('civix.source_record.source_record_id'), nullable=True),
        sa.Column('generation_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.generation_run.generation_run_id'), nullable=True),
        sa.ForeignKeyConstraint(['entity_id', 'entity_type'], ['civix.entity.entity_id', 'civix.entity.entity_type']),
        sa.CheckConstraint("entity_type = 'LOCATION'", name='chk_entity_type_location'),
        schema='civix'
    )
    
    op.execute("ALTER TABLE civix.location ADD COLUMN geometry GEOMETRY(Geometry, 4326) NOT NULL;")

def downgrade() -> None:
    pass
