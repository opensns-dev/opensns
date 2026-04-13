"""merge_provider_credential_and_settings_fields

Revision ID: 48636ff32783
Revises: 14fc5ae9d93a, 4a34eacc4f22
Create Date: 2026-04-09 06:44:00.218486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48636ff32783'
down_revision: Union[str, Sequence[str], None] = ('14fc5ae9d93a', '4a34eacc4f22')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
