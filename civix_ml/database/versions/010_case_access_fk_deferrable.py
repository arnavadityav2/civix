"""case_access_fk_deferrable

Revision ID: b470de0f178b
Revises: 009
Create Date: 2026-08-30 07:30:09.318580

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, Sequence[str], None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint('case_access_case_id_fkey', 'case_access', schema='civix', type_='foreignkey')
    op.create_foreign_key(
        'case_access_case_id_fkey',
        'case_access', 'investigative_case',
        ['case_id'], ['case_id'],
        source_schema='civix', referent_schema='civix',
        deferrable=True, initially='DEFERRED'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('case_access_case_id_fkey', 'case_access', schema='civix', type_='foreignkey')
    op.create_foreign_key(
        'case_access_case_id_fkey',
        'case_access', 'investigative_case',
        ['case_id'], ['case_id'],
        source_schema='civix', referent_schema='civix',
        deferrable=False
    )
