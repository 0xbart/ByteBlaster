"""tags + sound_tags

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-15

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tags",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(32), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "sound_tags",
        sa.Column(
            "sound_id",
            sa.Integer,
            sa.ForeignKey("sounds.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "tag_id",
            sa.Integer,
            sa.ForeignKey("tags.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )
    op.create_index("ix_sound_tags_tag_id", "sound_tags", ["tag_id"])


def downgrade() -> None:
    op.drop_index("ix_sound_tags_tag_id", table_name="sound_tags")
    op.drop_table("sound_tags")
    op.drop_table("tags")
