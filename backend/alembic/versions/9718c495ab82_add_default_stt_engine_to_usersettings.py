"""add_default_stt_engine_to_usersettings

Revision ID: 9718c495ab82
Revises: f86fb3378b23
Create Date: 2026-04-20 15:38:12.763663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '9718c495ab82'
down_revision: Union[str, Sequence[str], None] = 'f86fb3378b23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if _column_exists("usersettings", "default_stt_engine"):
        return

    op.add_column(
        "usersettings",
        sa.Column(
            "default_stt_engine",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="openai-stt",
        ),
    )


def downgrade() -> None:
    op.drop_column("usersettings", "default_stt_engine")
