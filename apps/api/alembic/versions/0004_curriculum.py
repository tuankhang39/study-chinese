"""curriculum tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-26
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("title_en", sa.String(length=200), nullable=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("hsk_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_courses_slug", "courses", ["slug"], unique=True)
    op.create_index("ix_courses_hsk_level", "courses", ["hsk_level"])

    op.create_table(
        "lessons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title_zh", sa.String(length=200), nullable=False),
        sa.Column("title_vi", sa.String(length=200), nullable=True),
        sa.Column("title_en", sa.String(length=200), nullable=True),
        sa.Column("objectives", sa.JSON(), nullable=True),
        sa.Column("grammar_points", sa.JSON(), nullable=True),
        sa.Column("page_start", sa.Integer(), nullable=True),
        sa.Column("page_end", sa.Integer(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=512), nullable=True),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.UniqueConstraint("course_id", "number", name="uq_course_lesson_number"),
    )
    op.create_index("ix_lessons_course_id", "lessons", ["course_id"])

    op.create_table(
        "lesson_sections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("section_type", sa.String(length=32), nullable=False, server_default="other"),
        sa.Column("title", sa.String(length=240), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("content_json", sa.JSON(), nullable=True),
        sa.Column("image_url", sa.String(length=512), nullable=True),
        sa.Column("page_ref", sa.Integer(), nullable=True),
    )
    op.create_index("ix_lesson_sections_lesson_id", "lesson_sections", ["lesson_id"])
    op.create_index("ix_lesson_sections_section_type", "lesson_sections", ["section_type"])

    op.create_table(
        "lesson_progress",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lesson_id", sa.Integer(), sa.ForeignKey("lessons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("completed_section_ids", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),
    )
    op.create_index("ix_lesson_progress_user_id", "lesson_progress", ["user_id"])
    op.create_index("ix_lesson_progress_lesson_id", "lesson_progress", ["lesson_id"])


def downgrade() -> None:
    op.drop_table("lesson_progress")
    op.drop_table("lesson_sections")
    op.drop_table("lessons")
    op.drop_table("courses")
