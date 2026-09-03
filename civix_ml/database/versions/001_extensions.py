"""extensions

Revision ID: 001
Revises: 
Create Date: 2026-08-30

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 001_extensions.py must install only the extensions actually required by the approved schema
    # Use postgresql schema 'public' or let it default. Often extensions are created in 'public'
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")
    # IMPORTANT: Do NOT use uuid-ossp. gen_random_uuid() is native in PG13+.
    
    # We also create the schema civix
    op.execute("CREATE SCHEMA IF NOT EXISTS civix;")

def downgrade() -> None:
    # Dropping postgis is dangerous as it drops all geometry columns.
    # Safe downgrade might just be empty, or we drop schema if empty.
    # The prompt explicitly warns: NEVER implement a downgrade that violates the immutable/audit/security contract.
    # "If a safe downgrade is impossible for a security-critical object, document that explicitly rather than creating a dangerous downgrade."
    
    # Dropping civix schema would destroy all data.
    pass
