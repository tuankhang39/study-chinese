"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-25
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("xp", sa.Integer(), server_default="0"),
        sa.Column("level", sa.Integer(), server_default="1"),
        sa.Column("streak", sa.Integer(), server_default="0"),
        sa.Column("last_active_date", sa.Date(), nullable=True),
        sa.Column("ai_messages_today", sa.Integer(), server_default="0"),
        sa.Column("ai_messages_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "vocabulary",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("hanzi", sa.String(64), nullable=False),
        sa.Column("traditional", sa.String(64), nullable=True),
        sa.Column("pinyin", sa.String(128), nullable=False),
        sa.Column("meaning_vi", sa.Text(), nullable=False),
        sa.Column("meaning_en", sa.Text(), nullable=True),
        sa.Column("hsk_level", sa.Integer(), nullable=False),
        sa.Column("part_of_speech", sa.String(64), nullable=True),
        sa.Column("frequency", sa.Integer(), nullable=True),
        sa.Column("example_zh", sa.Text(), nullable=True),
        sa.Column("example_vi", sa.Text(), nullable=True),
    )
    op.create_index("ix_vocabulary_hanzi", "vocabulary", ["hanzi"])
    op.create_index("ix_vocabulary_hsk_level", "vocabulary", ["hsk_level"])

    op.create_table(
        "scenarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("track", sa.String(32), nullable=False),
        sa.Column("job_tag", sa.String(64), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("prompt_system", sa.Text(), nullable=False),
        sa.Column("starter_lines", sa.JSON(), nullable=False),
        sa.Column("difficulty", sa.Integer(), server_default="1"),
    )

    op.create_table(
        "user_cards",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("vocab_id", sa.Integer(), sa.ForeignKey("vocabulary.id", ondelete="CASCADE")),
        sa.Column("due", sa.DateTime(timezone=True), nullable=False),
        sa.Column("stability", sa.Float(), server_default="0"),
        sa.Column("difficulty", sa.Float(), server_default="0"),
        sa.Column("elapsed_days", sa.Integer(), server_default="0"),
        sa.Column("scheduled_days", sa.Integer(), server_default="0"),
        sa.Column("reps", sa.Integer(), server_default="0"),
        sa.Column("lapses", sa.Integer(), server_default="0"),
        sa.Column("state", sa.Integer(), server_default="0"),
        sa.Column("last_review", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "vocab_id", name="uq_user_vocab"),
    )

    op.create_table(
        "daily_missions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("mission_date", sa.Date(), nullable=False),
        sa.Column("tasks", sa.JSON(), nullable=False),
        sa.Column("completed", sa.Boolean(), server_default="false"),
        sa.Column("xp_awarded", sa.Integer(), server_default="0"),
        sa.UniqueConstraint("user_id", "mission_date", name="uq_user_mission_date"),
    )

    op.create_table(
        "roleplay_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id", ondelete="CASCADE")),
        sa.Column("messages", sa.JSON(), nullable=False),
        sa.Column("scores", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "xp_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE")),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("xp_events")
    op.drop_table("roleplay_sessions")
    op.drop_table("daily_missions")
    op.drop_table("user_cards")
    op.drop_table("scenarios")
    op.drop_table("vocabulary")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
