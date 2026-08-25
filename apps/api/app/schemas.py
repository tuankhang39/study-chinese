from datetime import date, datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    xp: int
    level: int
    streak: int
    last_active_date: Optional[date] = None

    class Config:
        from_attributes = True


class VocabOut(BaseModel):
    id: int
    hanzi: str
    traditional: Optional[str] = None
    pinyin: str
    meaning_vi: str
    meaning_en: Optional[str] = None
    hsk_level: int
    part_of_speech: Optional[str] = None
    frequency: Optional[int] = None
    example_zh: Optional[str] = None
    example_vi: Optional[str] = None

    class Config:
        from_attributes = True


class CardOut(BaseModel):
    id: int
    due: datetime
    reps: int
    lapses: int
    state: int
    vocab: VocabOut

    class Config:
        from_attributes = True


class ReviewRequest(BaseModel):
    rating: Literal["again", "hard", "good", "easy"]


class MissionTask(BaseModel):
    id: str
    title: str
    xp: int
    done: bool = False
    target: int = 1
    progress: int = 0


class MissionOut(BaseModel):
    id: int
    mission_date: date
    tasks: list[MissionTask]
    completed: bool
    xp_awarded: int

    class Config:
        from_attributes = True


class CompleteMissionTaskRequest(BaseModel):
    task_id: str
    increment: int = 1


class ScenarioOut(BaseModel):
    id: int
    track: str
    job_tag: Optional[str] = None
    title: str
    description: str
    starter_lines: list[Any]
    difficulty: int

    class Config:
        from_attributes = True


class RoleplayCreateRequest(BaseModel):
    scenario_id: int


class RoleplayMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class RoleplayScores(BaseModel):
    grammar: Optional[int] = None
    vocabulary: Optional[int] = None
    naturalness: Optional[int] = None
    corrected_zh: Optional[str] = None
    corrected_vi: Optional[str] = None
    feedback_vi: Optional[str] = None


class RoleplaySessionOut(BaseModel):
    id: int
    scenario_id: int
    messages: list[Any]
    scores: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class ListeningItemOut(BaseModel):
    vocab: VocabOut
    options: list[str]
    answer_index: int


class HomeOut(BaseModel):
    user: UserOut
    mission: MissionOut
    due_count: int
    continue_track: Literal["hsk", "work"]
    tip: str
