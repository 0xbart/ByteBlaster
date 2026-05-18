"""admin role and categories

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-15

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column(
        "users",
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(64), nullable=False, unique=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.add_column(
        "sounds",
        sa.Column(
            "category_id",
            sa.Integer,
            sa.ForeignKey("categories.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Promote the oldest existing user to superadmin so the dev DB keeps an
    # admin after migration. No-op on an empty DB.
    op.execute(
        """
        UPDATE users
           SET is_admin = TRUE, is_superadmin = TRUE
         WHERE id = (SELECT id FROM users ORDER BY id ASC LIMIT 1)
        """
    )


def downgrade() -> None:
    op.drop_column("sounds", "category_id")
    op.drop_table("categories")
    op.drop_column("users", "is_superadmin")
    op.drop_column("users", "is_admin")
