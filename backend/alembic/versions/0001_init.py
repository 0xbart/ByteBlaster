"""init

Revision ID: 0001
Revises:
Create Date: 2026-05-15

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET


revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("username", sa.String(64), nullable=False, unique=True),
        sa.Column("ip", INET(), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "sounds",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("original_filename", sa.String(255)),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column(
            "uploaded_by_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_sounds_created_at_desc", "sounds", [sa.text("created_at DESC")])

    op.create_table(
        "plays",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "sound_id",
            sa.Integer,
            sa.ForeignKey("sounds.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "played_by_user_id",
            sa.Integer,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "played_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_plays_played_at_desc", "plays", [sa.text("played_at DESC")])


def downgrade() -> None:
    op.drop_index("ix_plays_played_at_desc", table_name="plays")
    op.drop_table("plays")
    op.drop_index("ix_sounds_created_at_desc", table_name="sounds")
    op.drop_table("sounds")
    op.drop_table("users")
