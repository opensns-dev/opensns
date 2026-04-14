"""add_tts_bgm_audio_settings_columns

Revision ID: f86fb3378b23
Revises: 1b9a048349b4
Create Date: 2026-04-14 19:36:56.691417

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


revision: str = "f86fb3378b23"
down_revision: Union[str, Sequence[str], None] = "1b9a048349b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    if _column_exists("usersettings", "default_tts_engine"):
        return

    op.add_column(
        "usersettings",
        sa.Column(
            "default_tts_engine",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="openai-tts",
        ),
    )
    op.add_column(
        "usersettings",
        sa.Column(
            "default_bgm_engine",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default="static-bgm",
        ),
    )
    op.add_column(
        "usersettings",
        sa.Column(
            "tts_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "usersettings",
        sa.Column(
            "bgm_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "usersettings",
        sa.Column(
            "tts_voice_id",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )
    op.add_column(
        "usersettings",
        sa.Column(
            "bgm_style",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("usersettings", "bgm_style")
    op.drop_column("usersettings", "tts_voice_id")
    op.drop_column("usersettings", "bgm_enabled")
    op.drop_column("usersettings", "tts_enabled")
    op.drop_column("usersettings", "default_bgm_engine")
    op.drop_column("usersettings", "default_tts_engine")
