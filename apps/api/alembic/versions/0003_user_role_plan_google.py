"""user role, plan, google_sub

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=32), server_default="user", nullable=False))
    op.add_column("users", sa.Column("plan", sa.String(length=32), server_default="free", nullable=False))
    op.add_column("users", sa.Column("google_sub", sa.String(length=128), nullable=True))
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_plan", "users", ["plan"])
    op.create_index("ix_users_google_sub", "users", ["google_sub"], unique=True)
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=True)


def downgrade() -> None:
    op.alter_column("users", "password_hash", existing_type=sa.String(length=255), nullable=False)
    op.drop_index("ix_users_google_sub", table_name="users")
    op.drop_index("ix_users_plan", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "google_sub")
    op.drop_column("users", "plan")
    op.drop_column("users", "role")
