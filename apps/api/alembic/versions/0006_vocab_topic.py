"""add vocabulary.topic

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("vocabulary", sa.Column("topic", sa.String(length=64), nullable=True))
    op.create_index("ix_vocabulary_topic", "vocabulary", ["topic"])


def downgrade() -> None:
    op.drop_index("ix_vocabulary_topic", table_name="vocabulary")
    op.drop_column("vocabulary", "topic")
