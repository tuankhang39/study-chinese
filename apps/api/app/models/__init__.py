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
    password_hash: Mapped[str] = mapped_column(String(255))
    display_name: Mapped[str] = mapped_column(String(120))
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
