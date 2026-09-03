"""security_audit

Revision ID: 009
Revises: 008
Create Date: 2026-08-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM, UUID, TIMESTAMP, TSTZRANGE, JSONB
from sqlalchemy.dialects.postgresql.base import INET

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 1. civix.legal_restriction
    op.create_table(
        'legal_restriction',
        sa.Column('restriction_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('target_entity_id', UUID(as_uuid=True), sa.ForeignKey('civix.entity.entity_id'), nullable=True),
        sa.Column('target_artifact_id', UUID(as_uuid=True), sa.ForeignKey('civix.evidence_artifact.artifact_id'), nullable=True),
        sa.Column('restriction_type', ENUM(name='legal_restriction_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('authority', sa.Text(), nullable=False),
        sa.Column('court_order_reference', sa.Text(), nullable=True),
        sa.Column('effective_range', TSTZRANGE(), nullable=False),
        sa.Column('scope', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='ACTIVE'),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('lifted_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('lifted_at', TIMESTAMP(timezone=True), nullable=True),
        schema='civix'
    )
    op.create_check_constraint('chk_restriction_target', 'legal_restriction', 'target_entity_id IS NOT NULL OR target_artifact_id IS NOT NULL', schema='civix')

    # 2. civix.audit_event
    op.create_table(
        'audit_event',
        sa.Column('audit_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=False),
        sa.Column('action', ENUM(name='audit_action_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('target_table', sa.Text(), nullable=False),
        sa.Column('target_id', UUID(as_uuid=True), nullable=False),
        sa.Column('case_context_id', UUID(as_uuid=True), sa.ForeignKey('civix.investigative_case.case_id'), nullable=True),
        sa.Column('ip_address', INET(), nullable=True),
        sa.Column('timestamp', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('metadata', JSONB(), nullable=True),
        schema='civix'
    )

    # 3. civix.outbox
    op.create_table(
        'outbox',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.Text(), nullable=False),
        sa.Column('payload', JSONB(), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('consumed_at', TIMESTAMP(timezone=True), nullable=True),
        schema='civix'
    )

    # 4. civix.provenance
    op.create_table(
        'provenance',
        sa.Column('provenance_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('derived_type', sa.Text(), nullable=False),
        sa.Column('derived_id', UUID(as_uuid=True), nullable=False),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_id', UUID(as_uuid=True), nullable=False),
        sa.Column('derivation_method', sa.Text(), nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        schema='civix'
    )

    # 5. civix.data_quality_issue
    op.create_table(
        'data_quality_issue',
        sa.Column('issue_id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('affected_entity_type', sa.Text(), nullable=False),
        sa.Column('affected_entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('issue_type', ENUM(name='data_quality_issue_type_enum', schema='civix', create_type=False), nullable=False),
        sa.Column('severity', sa.Text(), nullable=False),
        sa.Column('detected_by', sa.Text(), nullable=False),
        sa.Column('detection_run_id', UUID(as_uuid=True), sa.ForeignKey('civix.analysis_run.run_id'), nullable=True),
        sa.Column('detected_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.Text(), nullable=False, server_default='OPEN'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by', UUID(as_uuid=True), sa.ForeignKey('civix.civix_user.user_id'), nullable=True),
        sa.Column('resolved_at', TIMESTAMP(timezone=True), nullable=True),
        schema='civix'
    )

    # ==========================
    # TRIGGERS
    # ==========================
    
    # Trigger 1: Immutable / Append Only
    op.execute("""
    CREATE OR REPLACE FUNCTION civix.block_mutation()
    RETURNS TRIGGER AS $$
    BEGIN
        RAISE EXCEPTION 'Updates and deletions are strictly forbidden on this immutable audit table.';
    END;
    $$ LANGUAGE plpgsql;
    """)

    immutable_tables = [
        'audit_event', 'source_record', 'evidence_artifact', 'identity_resolution',
        'identity_merge_event', 'identity_split_event', 'legal_restriction', 'provenance'
    ]
    for tbl in immutable_tables:
        op.execute(f"""
        CREATE TRIGGER block_mutation_trigger
        BEFORE UPDATE OR DELETE ON civix.{tbl}
        FOR EACH ROW EXECUTE FUNCTION civix.block_mutation();
        """)

    # Trigger 2: Synthetic-Deletable Operational Tables
    op.execute("""
    CREATE OR REPLACE FUNCTION civix.block_operational_delete()
    RETURNS TRIGGER AS $$
    BEGIN
        IF OLD.generation_run_id IS NULL THEN
            RAISE EXCEPTION 'Operational deletion of non-synthetic records is strictly forbidden.';
        END IF;
        RETURN OLD;
    END;
    $$ LANGUAGE plpgsql;
    """)

    operational_tables = [
        'person', 'phone_number', 'sim', 'device', 'vehicle', 'property',
        'financial_account', 'organization', 'network', 'location',
        'case_entity_role', 'fir', 'case_link', 'observation', 'extraction',
        'event', 'event_participant', 'hypothesis', 'hypothesis_support',
        'investigative_lead', 'investigation_task', 'forensic_report', 'medical_report',
        'sim_number_assignment', 'sim_in_device', 'account_holder', 'assertion'
    ]
    for tbl in operational_tables:
        op.execute(f"""
        CREATE TRIGGER enforce_no_delete_unless_synthetic
        BEFORE DELETE ON civix.{tbl}
        FOR EACH ROW EXECUTE FUNCTION civix.block_operational_delete();
        """)

    # ==========================
    # ROW-LEVEL SECURITY (RLS)
    # ==========================
    # Helper to apply RLS
    def apply_rls(table_name, using_clause, with_check_clause=None):
        if with_check_clause is None:
            with_check_clause = using_clause
        op.execute(f"ALTER TABLE civix.{table_name} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE civix.{table_name} FORCE ROW LEVEL SECURITY;")
        op.execute(f"""
        CREATE POLICY {table_name}_access_policy ON civix.{table_name}
        FOR ALL
        USING ({using_clause})
        WITH CHECK ({with_check_clause});
        """)

    # 1. Direct case-scoped
    direct_tables = ['investigative_case', 'case_entity_role', 'evidence_instance', 'fir', 'hypothesis', 'investigative_lead', 'investigation_task']
    for tbl in direct_tables:
        # For investigative_case, the id is case_id. For others it's case_id.
        apply_rls(tbl, f"""
        EXISTS (
            SELECT 1 FROM civix.case_access 
            WHERE case_id = {tbl}.case_id 
            AND user_id = current_setting('civix.current_user_id', true)::uuid 
            AND is_revoked = false
        )
        """)

    # 2. case_link
    apply_rls('case_link', """
    EXISTS (
        SELECT 1 FROM civix.case_access 
        WHERE case_id = case_link.source_case_id 
        AND user_id = current_setting('civix.current_user_id', true)::uuid 
        AND is_revoked = false
    )
    """)

    # 3. hypothesis_support -> hypothesis -> case_id
    apply_rls('hypothesis_support', """
    EXISTS (
        SELECT 1 FROM civix.hypothesis h
        JOIN civix.case_access ca ON h.case_id = ca.case_id
        WHERE h.hypothesis_id = hypothesis_support.hypothesis_id
        AND ca.user_id = current_setting('civix.current_user_id', true)::uuid 
        AND ca.is_revoked = false
    )
    """)

    # 4. Indirect via evidence_instance: medical_report, forensic_report, observation, extraction
    evidence_indirect = ['medical_report', 'forensic_report', 'observation', 'extraction']
    for tbl in evidence_indirect:
        apply_rls(tbl, f"""
        EXISTS (
            SELECT 1 FROM civix.evidence_instance e
            JOIN civix.case_access ca ON e.case_id = ca.case_id
            WHERE e.instance_id = {tbl}.instance_id
            AND ca.user_id = current_setting('civix.current_user_id', true)::uuid 
            AND ca.is_revoked = false
        )
        """)


def downgrade() -> None:
    pass
