"""enums

Revision ID: 002
Revises: 001
Create Date: 2026-08-30

"""
from alembic import op
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # We will create PostgreSQL ENUM types in the civix schema.
    
    enums = {
        'entity_type_enum': [
            'PERSON', 'SOURCE_IDENTITY', 'PHONE_NUMBER', 'SIM', 'DEVICE',
            'FINANCIAL_ACCOUNT', 'VEHICLE', 'PROPERTY', 'ORGANIZATION', 'NETWORK', 'LOCATION'
        ],
        'source_identity_type_enum': [
            'NAME', 'PHONE_MSISDN', 'IMEI', 'MAC_ADDRESS', 'VEHICLE_REG',
            'EMAIL', 'FACE_EMBEDDING_REF', 'FINGERPRINT_REF', 'VOICE_PRINT_REF',
            'AADHAAR_MASKED', 'PAN_MASKED', 'DRIVING_LICENSE', 'PASSPORT_NUMBER', 'OTHER'
        ],
        'predicate_enum': [
            'CALLED', 'MESSAGED', 'PINGED_TOWER', 'USED_DEVICE', 'USED_SIM',
            'HAD_NUMBER', 'SEEN_AT', 'PRESENT_AT', 'TRANSFERRED_TO', 'TRANSFERRED_FROM',
            'HOLDS_ACCOUNT', 'OWNS', 'OWNED', 'TRANSFERRED_OWNERSHIP_OF',
            'RECEIVED_PROPERTY', 'REGISTERED_TO', 'DRIVER_OF', 'PASSENGER_IN',
            'MEMBER_OF', 'EMPLOYED_BY', 'KNOWN_ASSOCIATE_OF', 'RESIDED_AT', 'VISITED',
            'ALIBI_CONFIRMED_AT', 'DNA_MATCHES', 'DNA_EXCLUDED',
            'FINGERPRINT_MATCHES', 'FINGERPRINT_EXCLUDED',
            'FACE_MATCHES', 'VEHICLE_REG_MATCHES',
            'TIME_OF_DEATH_IS', 'CAUSE_OF_DEATH_IS', 'HAS_INJURY',
            'LOCATED_AT', 'REGISTERED_AT'
        ],
        'participant_role_enum': [
            'CALLER', 'CALLEE', 'PING_SOURCE', 'DRIVER', 'PASSENGER', 'REGISTERED_OWNER',
            'SENDER', 'RECEIVER', 'ACCOUNT_HOLDER', 'JOINT_HOLDER', 'BENEFICIARY',
            'PREVIOUS_OWNER', 'NEW_OWNER', 'TARGET_PROPERTY', 'REGISTRAR',
            'LOCATION', 'CELL_TOWER', 'VICTIM', 'SUSPECT', 'WITNESS', 'OFFICER',
            'OBSERVER', 'SUBJECT', 'COMPLAINANT', 'SAMPLE_COLLECTOR',
            'EXAMINER', 'CUSTODIAN', 'PARTICIPANT'
        ],
        'epistemic_status_enum': [
            'POSSIBLE', 'PROBABLE', 'CONFIRMED', 'REFUTED', 'INCONCLUSIVE'
        ],
        'support_stance_enum': [
            'SUPPORT', 'CONTRADICT', 'NEUTRAL', 'INCONCLUSIVE'
        ],
        'identity_resolution_status_enum': [
            'ACCEPTED', 'REJECTED', 'SUPERSEDED', 'UNRESOLVED', 'REVIEW_REQUIRED'
        ],
        'event_type_enum': [
            'CALL', 'MESSAGE', 'TRANSACTION', 'VEHICLE_SIGHTING', 'PROPERTY_MUTATION',
            'MEETING', 'SEIZURE', 'ARREST', 'SURVEILLANCE_OBSERVATION',
            'FORENSIC_COLLECTION', 'MEDICAL_EXAMINATION', 'FIR_FILING',
            'DEVICE_PING', 'BORDER_CROSSING', 'OTHER'
        ],
        'case_type_enum': [
            'CRIMINAL', 'INTELLIGENCE', 'PROPERTY', 'FINANCIAL', 'SURVEILLANCE',
            'FORENSIC', 'MULTI_CASE'
        ],
        'case_status_enum': [
            'OPEN', 'ACTIVE', 'SUSPENDED', 'CLOSED_SOLVED', 'CLOSED_UNSOLVED', 'ARCHIVED'
        ],
        'case_priority_enum': [
            'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        ],
        'case_entity_role_enum': [
            'SUSPECT', 'VICTIM', 'COMPLAINANT', 'WITNESS', 'PERSON_OF_INTEREST',
            'ACCUSED', 'ACQUITTED', 'OFFICER_IN_CHARGE', 'INFORMANT',
            'SUBJECT_ORG', 'SUBJECT_VEHICLE', 'SUBJECT_ACCOUNT',
            'SUBJECT_PROPERTY', 'SUBJECT_DEVICE', 'RELATED_PERSON'
        ],
        'civix_role_enum': [
            'INVESTIGATOR', 'SUPERVISOR', 'ANALYST', 'ADMIN',
            'FORENSIC_EXAMINER', 'LEGAL_OFFICER', 'READ_ONLY'
        ],
        'clearance_enum': [
            'UNCLASSIFIED', 'RESTRICTED', 'CONFIDENTIAL', 'SECRET'
        ],
        'case_permission_enum': [
            'READ', 'WRITE', 'ADMIN'
        ],
        'audit_action_enum': [
            'LOGIN', 'LOGOUT', 'READ', 'WRITE', 'EXPORT', 'RESTRICT',
            'LIFT_RESTRICTION', 'IDENTITY_RESOLVE', 'HYPOTHESIS_STATUS_CHANGE',
            'LEAD_DISPOSITION', 'ADMIN_ACTION', 'TOMBSTONE_ISSUED'
        ],
        'legal_restriction_type_enum': [
            'EXPUNGED', 'SEALED', 'JUVENILE_PROTECTED', 'COURT_RESTRICTED',
            'CLASSIFIED', 'NATIONAL_SECURITY'
        ],
        'data_quality_issue_type_enum': [
            'IMPOSSIBLE_TIMESTAMP', 'MALFORMED_RECORD', 'DUPLICATE_RECORD',
            'MISSING_REQUIRED_FIELD', 'CONTRADICTORY_DATA', 'CUSTODY_GAP',
            'UNKNOWN_IDENTIFIER', 'HASH_MISMATCH', 'SPATIAL_IMPOSSIBILITY',
            'TEMPORAL_IMPOSSIBILITY', 'OTHER'
        ],
        'location_type_enum': [
            'EXACT_POINT', 'ESTIMATED_POINT', 'CELL_SECTOR_POLYGON',
            'CCTV_COVERAGE_POLYGON', 'PROPERTY_BOUNDARY', 'CRIME_SCENE',
            'GEOFENCE', 'ADMIN_BOUNDARY', 'ROUTE_LINESTRING'
        ],
        'hash_algorithm_enum': [
            'SHA256', 'SHA512', 'SHA3_256', 'MD5_DEPRECATED'
        ],
        'extraction_type_enum': [
            'FACE_DETECTION', 'OCR', 'ANPR', 'NER', 'RELATIONSHIP_EXTRACTION',
            'ANOMALY_DETECTION', 'CLUSTERING', 'VOICE_PRINT',
            'FINGERPRINT_MATCH', 'GEOLOCATION_INFERENCE', 'TEMPORAL_INFERENCE', 'OTHER'
        ],
        'dataset_type_enum': [
            'GOLDEN_WORLD', 'SYNTHETIC_TRAIN', 'SYNTHETIC_VAL',
            'SYNTHETIC_TEST', 'PRODUCTION'
        ],
        'hypothesis_status_enum': [
            'ACTIVE', 'UNDER_REVIEW', 'CONFIRMED', 'REFUTED', 'ARCHIVED'
        ],
        'lead_priority_enum': [
            'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        ],
        'lead_status_enum': [
            'OPEN', 'IN_PROGRESS', 'CONFIRMED', 'FALSE_POSITIVE', 'CLOSED', 'DEFERRED'
        ],
        'task_type_enum': [
            'INTERVIEW', 'SURVEILLANCE', 'SEARCH_AND_SEIZURE', 'FORENSIC_COLLECTION',
            'FINANCIAL_REVIEW', 'LEGAL_REQUEST', 'COURT_ORDER', 'DATA_ANALYSIS',
            'FIELD_VERIFICATION', 'OTHER'
        ],
        'task_status_enum': [
            'PENDING', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'BLOCKED'
        ]
    }

    for enum_name, values in enums.items():
        enum_type = ENUM(*values, name=enum_name, schema='civix')
        enum_type.create(op.get_bind())

def downgrade() -> None:
    # Not dropping enums in downgrade as they might be used by other objects,
    # or it's non-trivial. 
    # Just leaving pass to adhere to safe downgrade policy.
    pass
