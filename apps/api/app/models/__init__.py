from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_name: Mapped[str] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(32), default="user", index=True)  # user|admin|super_admin
    plan: Mapped[str] = mapped_column(String(32), default="free", index=True)  # free|pro|unlimit
    google_sub: Mapped[Optional[str]] = mapped_column(String(128), unique=True, nullable=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    level: Mapped[int] = mapped_column(Integer, default=1)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    ai_messages_today: Mapped[int] = mapped_column(Integer, default=0)
    ai_messages_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    cards: Mapped[list[UserCard]] = relationship(back_populates="user")
    missions: Mapped[list[DailyMission]] = relationship(back_populates="user")
    roleplay_sessions: Mapped[list[RoleplaySession]] = relationship(back_populates="user")
    xp_events: Mapped[list[XpEvent]] = relationship(back_populates="user")


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hanzi: Mapped[str] = mapped_column(String(64), index=True)
    traditional: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    pinyin: Mapped[str] = mapped_column(String(128))
    meaning_vi: Mapped[str] = mapped_column(Text)
    meaning_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hsk_level: Mapped[int] = mapped_column(Integer, index=True)
    part_of_speech: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    frequency: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    example_zh: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    cards: Mapped[list[UserCard]] = relationship(back_populates="vocab")


class UserCard(Base):
    __tablename__ = "user_cards"
    __table_args__ = (UniqueConstraint("user_id", "vocab_id", name="uq_user_vocab"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    vocab_id: Mapped[int] = mapped_column(ForeignKey("vocabulary.id", ondelete="CASCADE"), index=True)
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    stability: Mapped[float] = mapped_column(Float, default=0.0)
    difficulty: Mapped[float] = mapped_column(Float, default=0.0)
    elapsed_days: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_days: Mapped[int] = mapped_column(Integer, default=0)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    state: Mapped[int] = mapped_column(Integer, default=0)  # 0=New,1=Learning,2=Review,3=Relearning
    last_review: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped[User] = relationship(back_populates="cards")
    vocab: Mapped[Vocabulary] = relationship(back_populates="cards")


class Scenario(Base):
    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    track: Mapped[str] = mapped_column(String(32), index=True)  # hsk | work
    job_tag: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    prompt_system: Mapped[str] = mapped_column(Text)
    starter_lines: Mapped[list[Any]] = mapped_column(JSON, default=list)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)

    sessions: Mapped[list[RoleplaySession]] = relationship(back_populates="scenario")


class DailyMission(Base):
    __tablename__ = "daily_missions"
    __table_args__ = (UniqueConstraint("user_id", "mission_date", name="uq_user_mission_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    mission_date: Mapped[date] = mapped_column(Date, index=True)
    tasks: Mapped[list[Any]] = mapped_column(JSON, default=list)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_awarded: Mapped[int] = mapped_column(Integer, default=0)

    user: Mapped[User] = relationship(back_populates="missions")


class RoleplaySession(Base):
    __tablename__ = "roleplay_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), index=True)
    messages: Mapped[list[Any]] = mapped_column(JSON, default=list)
    scores: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="roleplay_sessions")
    scenario: Mapped[Scenario] = relationship(back_populates="sessions")


class XpEvent(Base):
    __tablename__ = "xp_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="xp_events")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    title_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    hsk_level: Mapped[int] = mapped_column(Integer, default=1, index=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    coming_soon: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    lessons: Mapped[list[Lesson]] = relationship(
        back_populates="course", cascade="all, delete-orphan", order_by="Lesson.number"
    )


class Lesson(Base):
    __tablename__ = "lessons"
    __table_args__ = (UniqueConstraint("course_id", "number", name="uq_course_lesson_number"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    title_zh: Mapped[str] = mapped_column(String(200))
    title_vi: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    title_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    lesson_type: Mapped[str] = mapped_column(String(32), default="dialogue_core", index=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=12)
    unlock_rule: Mapped[str] = mapped_column(String(32), default="sequential")  # sequential|open
    objectives: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    grammar_points: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    page_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    page_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True)

    course: Mapped[Course] = relationship(back_populates="lessons")
    sections: Mapped[list[LessonSection]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="LessonSection.sort_order"
    )
    steps: Mapped[list[LessonStep]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan", order_by="LessonStep.sort_order"
    )
    vocab_links: Mapped[list[LessonVocab]] = relationship(
        back_populates="lesson", cascade="all, delete-orphan"
    )
    progress_rows: Mapped[list[LessonProgress]] = relationship(back_populates="lesson")


class LessonSection(Base):
    __tablename__ = "lesson_sections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    # objectives|tongue_twister|warmup|text|vocab|grammar|tip|exercise|activity|bonus|summary|other
    section_type: Mapped[str] = mapped_column(String(32), default="other", index=True)
    title: Mapped[str] = mapped_column(String(240), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    content_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    page_ref: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    lesson: Mapped[Lesson] = relationship(back_populates="sections")


class LessonStep(Base):
    __tablename__ = "lesson_steps"
    __table_args__ = (UniqueConstraint("lesson_id", "step_key", name="uq_lesson_step_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    step_key: Mapped[str] = mapped_column(String(32), index=True)
    title_vi: Mapped[str] = mapped_column(String(120), default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    required: Mapped[bool] = mapped_column(Boolean, default=True)

    lesson: Mapped[Lesson] = relationship(back_populates="steps")
    items: Mapped[list[LessonItem]] = relationship(
        back_populates="step", cascade="all, delete-orphan", order_by="LessonItem.sort_order"
    )


class LessonItem(Base):
    __tablename__ = "lesson_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    step_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lesson_steps.id", ondelete="CASCADE"), nullable=True, index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    # vocab_card|sentence_card|dialogue_line|grammar_tip|quiz_prompt|media|objective
    item_type: Mapped[str] = mapped_column(String(32), default="vocab_card", index=True)
    hanzi: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    pinyin: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    meaning_vi: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meaning_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    audio_text: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    speaker: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    source_page: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    step: Mapped[Optional[LessonStep]] = relationship(back_populates="items")


class LessonVocab(Base):
    __tablename__ = "lesson_vocab"
    __table_args__ = (UniqueConstraint("lesson_id", "vocab_id", name="uq_lesson_vocab"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    vocab_id: Mapped[int] = mapped_column(ForeignKey("vocabulary.id", ondelete="CASCADE"), index=True)
    is_key: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    lesson: Mapped[Lesson] = relationship(back_populates="vocab_links")
    vocab: Mapped[Vocabulary] = relationship()


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    completed_section_ids: Mapped[list[Any]] = mapped_column(JSON, default=list)
    completed_step_keys: Mapped[list[Any]] = mapped_column(JSON, default=list)
    item_results: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    percent: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lesson: Mapped[Lesson] = relationship(back_populates="progress_rows")
