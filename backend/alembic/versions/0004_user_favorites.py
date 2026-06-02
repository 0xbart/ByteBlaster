"""sound_favorites — per-user favorite sounds

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-02

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sound_favorites",
        sa.Column(
            "user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "sound_id",
            sa.Integer,
            sa.ForeignKey("sounds.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_sound_favorites_user", "sound_favorites", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sound_favorites_user", table_name="sound_favorites")
    op.drop_table("sound_favorites")
