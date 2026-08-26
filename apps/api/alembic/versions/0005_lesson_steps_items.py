"""curriculum steps/items/progress

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("courses", sa.Column("coming_soon", sa.Boolean(), server_default=sa.text("false"), nullable=False))
    op.add_column("lessons", sa.Column("lesson_type", sa.String(length=32), server_default="dialogue_core", nullable=False))
    op.add_column("lessons", sa.Column("estimated_minutes", sa.Integer(), server_default="12", nullable=False))
    op.add_column("lessons", sa.Column("unlock_rule", sa.String(length=32), server_default="sequential", nullable=False))
    op.create_index("ix_lessons_lesson_type", "lessons", ["lesson_type"])

    op.create_table(
        "lesson_steps",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_key", sa.String(length=32), nullable=False),
        sa.Column("title_vi", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("lesson_id", "step_key", name="uq_lesson_step_key"),
    )
    op.create_index("ix_lesson_steps_lesson_id", "lesson_steps", ["lesson_id"])
    op.create_index("ix_lesson_steps_step_key", "lesson_steps", ["step_key"])

    op.create_table(
        "lesson_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("step_id", sa.Integer(), sa.ForeignKey("lesson_steps.id", ondelete="CASCADE"), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("item_type", sa.String(length=32), nullable=False, server_default="vocab_card"),
        sa.Column("hanzi", sa.String(length=512), nullable=True),
        sa.Column("pinyin", sa.String(length=512), nullable=True),
        sa.Column("meaning_vi", sa.Text(), nullable=True),
        sa.Column("meaning_en", sa.Text(), nullable=True),
        sa.Column("audio_text", sa.String(length=512), nullable=True),
        sa.Column("speaker", sa.String(length=120), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
    )
    op.create_index("ix_lesson_items_lesson_id", "lesson_items", ["lesson_id"])
    op.create_index("ix_lesson_items_step_id", "lesson_items", ["step_id"])
    op.create_index("ix_lesson_items_item_type", "lesson_items", ["item_type"])

    op.create_table(
        "lesson_vocab",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("vocab_id", sa.Integer(), sa.ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_key", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("lesson_id", "vocab_id", name="uq_lesson_vocab"),
    )
    op.create_index("ix_lesson_vocab_lesson_id", "lesson_vocab", ["lesson_id"])
    op.create_index("ix_lesson_vocab_vocab_id", "lesson_vocab", ["vocab_id"])

    op.add_column("lesson_progress", sa.Column("completed_step_keys", sa.JSON(), server_default="[]", nullable=False))
    op.add_column("lesson_progress", sa.Column("item_results", sa.JSON(), nullable=True))
    op.add_column("lesson_progress", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("lesson_progress", "completed_at")
    op.drop_column("lesson_progress", "item_results")
    op.drop_column("lesson_progress", "completed_step_keys")
    op.drop_table("lesson_vocab")
    op.drop_table("lesson_items")
    op.drop_table("lesson_steps")
    op.drop_index("ix_lessons_lesson_type", table_name="lessons")
    op.drop_column("lessons", "unlock_rule")
    op.drop_column("lessons", "estimated_minutes")
    op.drop_column("lessons", "lesson_type")
    op.drop_column("courses", "coming_soon")
