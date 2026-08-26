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
    role: str = "user"
    plan: str = "free"
    xp: int
    level: int
    streak: int
    last_active_date: Optional[date] = None

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    display_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    role: Optional[Literal["user", "admin", "super_admin"]] = None
    plan: Optional[Literal["free", "pro", "unlimit"]] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=128)


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=120)
    role: Literal["user", "admin"] = "user"
    plan: Literal["free", "pro", "unlimit"] = "free"


class AdminVocabCreate(BaseModel):
    hanzi: str = Field(min_length=1, max_length=64)
    traditional: Optional[str] = None
    pinyin: str = Field(min_length=1, max_length=128)
    meaning_vi: str = Field(min_length=1)
    meaning_en: Optional[str] = None
    hsk_level: int = Field(ge=1, le=6)
    part_of_speech: Optional[str] = None
    frequency: Optional[int] = None
    example_zh: Optional[str] = None
    example_vi: Optional[str] = None


class AdminVocabUpdate(BaseModel):
    hanzi: Optional[str] = Field(default=None, min_length=1, max_length=64)
    traditional: Optional[str] = None
    pinyin: Optional[str] = Field(default=None, min_length=1, max_length=128)
    meaning_vi: Optional[str] = Field(default=None, min_length=1)
    meaning_en: Optional[str] = None
    hsk_level: Optional[int] = Field(default=None, ge=1, le=6)
    part_of_speech: Optional[str] = None
    frequency: Optional[int] = None
    example_zh: Optional[str] = None
    example_vi: Optional[str] = None


class AdminScenarioCreate(BaseModel):
    track: str = Field(min_length=1, max_length=32)
    job_tag: Optional[str] = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    prompt_system: str = Field(min_length=1)
    starter_lines: list[Any] = Field(default_factory=list)
    difficulty: int = Field(default=1, ge=1, le=5)


class AdminScenarioUpdate(BaseModel):
    track: Optional[str] = Field(default=None, min_length=1, max_length=32)
    job_tag: Optional[str] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, min_length=1)
    prompt_system: Optional[str] = Field(default=None, min_length=1)
    starter_lines: Optional[list[Any]] = None
    difficulty: Optional[int] = Field(default=None, ge=1, le=5)


class AdminScenarioOut(BaseModel):
    id: int
    track: str
    job_tag: Optional[str] = None
    title: str
    description: str
    prompt_system: str
    starter_lines: list[Any]
    difficulty: int

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
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedUsers(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int


class PaginatedVocab(BaseModel):
    items: list[VocabOut]
    total: int
    page: int
    page_size: int


class PaginatedScenarios(BaseModel):
    items: list[AdminScenarioOut]
    total: int
    page: int
    page_size: int


class AdminDashboard(BaseModel):
    users: int
    vocab: int
    scenarios: int
    by_plan: dict[str, int]
    by_role: dict[str, int]
    users_new_7d: int = 0
    google_users: int = 0
    roleplay_sessions: int = 0
    user_cards: int = 0
    by_hsk: dict[str, int] = {}
    paid_users: int = 0  # pro + unlimit


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


# ---- Curriculum / Giáo trình ----


class CourseOut(BaseModel):
    id: int
    slug: str
    title: str
    title_en: Optional[str] = None
    description: str = ""
    hsk_level: int = 1
    cover_image_url: Optional[str] = None
    published: bool = True
    coming_soon: bool = False
    sort_order: int = 0
    lesson_count: int = 0
    progress_percent: Optional[int] = None

    class Config:
        from_attributes = True


class CourseCreate(BaseModel):
    slug: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    title_en: Optional[str] = None
    description: str = ""
    hsk_level: int = Field(default=1, ge=1, le=6)
    cover_image_url: Optional[str] = None
    published: bool = True
    coming_soon: bool = False
    sort_order: int = 0


class CourseUpdate(BaseModel):
    slug: Optional[str] = Field(default=None, min_length=1, max_length=64)
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    title_en: Optional[str] = None
    description: Optional[str] = None
    hsk_level: Optional[int] = Field(default=None, ge=1, le=6)
    cover_image_url: Optional[str] = None
    published: Optional[bool] = None
    coming_soon: Optional[bool] = None
    sort_order: Optional[int] = None


class LessonSectionOut(BaseModel):
    id: int
    lesson_id: int
    sort_order: int
    section_type: str
    title: str
    content: str
    content_json: Optional[dict[str, Any]] = None
    image_url: Optional[str] = None
    page_ref: Optional[int] = None

    class Config:
        from_attributes = True


class LessonSectionCreate(BaseModel):
    lesson_id: int
    sort_order: int = 0
    section_type: str = "other"
    title: str = ""
    content: str = ""
    content_json: Optional[dict[str, Any]] = None
    image_url: Optional[str] = None
    page_ref: Optional[int] = None


class LessonSectionUpdate(BaseModel):
    sort_order: Optional[int] = None
    section_type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    content_json: Optional[dict[str, Any]] = None
    image_url: Optional[str] = None
    page_ref: Optional[int] = None


class LessonItemOut(BaseModel):
    id: int
    lesson_id: int
    step_id: Optional[int] = None
    sort_order: int = 0
    item_type: str
    hanzi: Optional[str] = None
    pinyin: Optional[str] = None
    meaning_vi: Optional[str] = None
    meaning_en: Optional[str] = None
    audio_text: Optional[str] = None
    speaker: Optional[str] = None
    image_url: Optional[str] = None
    source_page: Optional[int] = None
    meta: Optional[dict[str, Any]] = None

    class Config:
        from_attributes = True


class LessonItemCreate(BaseModel):
    lesson_id: int
    step_id: Optional[int] = None
    sort_order: int = 0
    item_type: str = "vocab_card"
    hanzi: Optional[str] = None
    pinyin: Optional[str] = None
    meaning_vi: Optional[str] = None
    meaning_en: Optional[str] = None
    audio_text: Optional[str] = None
    speaker: Optional[str] = None
    image_url: Optional[str] = None
    source_page: Optional[int] = None
    meta: Optional[dict[str, Any]] = None


class LessonItemUpdate(BaseModel):
    step_id: Optional[int] = None
    sort_order: Optional[int] = None
    item_type: Optional[str] = None
    hanzi: Optional[str] = None
    pinyin: Optional[str] = None
    meaning_vi: Optional[str] = None
    meaning_en: Optional[str] = None
    audio_text: Optional[str] = None
    speaker: Optional[str] = None
    image_url: Optional[str] = None
    source_page: Optional[int] = None
    meta: Optional[dict[str, Any]] = None


class LessonStepOut(BaseModel):
    id: int
    lesson_id: int
    step_key: str
    title_vi: str
    sort_order: int
    required: bool = True
    items: list[LessonItemOut] = []

    class Config:
        from_attributes = True


class LessonStepCreate(BaseModel):
    lesson_id: int
    step_key: str
    title_vi: str = ""
    sort_order: int = 0
    required: bool = True


class LessonStepUpdate(BaseModel):
    step_key: Optional[str] = None
    title_vi: Optional[str] = None
    sort_order: Optional[int] = None
    required: Optional[bool] = None


class LessonOut(BaseModel):
    id: int
    course_id: int
    number: int
    title_zh: str
    title_vi: Optional[str] = None
    title_en: Optional[str] = None
    title_pinyin: Optional[str] = None
    lesson_type: str = "dialogue_core"
    estimated_minutes: int = 12
    unlock_rule: str = "sequential"
    objectives: Optional[list[Any]] = None
    grammar_points: Optional[list[Any]] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    cover_image_url: Optional[str] = None
    published: bool = True
    section_count: int = 0
    step_count: int = 0
    locked: bool = False
    progress_percent: Optional[int] = None


class LessonDetailOut(LessonOut):
    sections: list[LessonSectionOut] = []
    steps: list[LessonStepOut] = []


class LessonPlayerOut(BaseModel):
    lesson: LessonOut
    steps: list[LessonStepOut]
    progress: "LessonProgressOut"
    next_lesson_id: Optional[int] = None
    source_pages: list[str] = []


class LessonCreate(BaseModel):
    course_id: int
    number: int = Field(ge=1)
    title_zh: str = Field(min_length=1, max_length=200)
    title_vi: Optional[str] = None
    title_en: Optional[str] = None
    lesson_type: str = "dialogue_core"
    estimated_minutes: int = 12
    unlock_rule: str = "sequential"
    objectives: Optional[list[Any]] = None
    grammar_points: Optional[list[Any]] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    cover_image_url: Optional[str] = None
    published: bool = True


class LessonUpdate(BaseModel):
    number: Optional[int] = Field(default=None, ge=1)
    title_zh: Optional[str] = Field(default=None, min_length=1, max_length=200)
    title_vi: Optional[str] = None
    title_en: Optional[str] = None
    lesson_type: Optional[str] = None
    estimated_minutes: Optional[int] = None
    unlock_rule: Optional[str] = None
    objectives: Optional[list[Any]] = None
    grammar_points: Optional[list[Any]] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    cover_image_url: Optional[str] = None
    published: Optional[bool] = None


class LessonProgressOut(BaseModel):
    lesson_id: int
    completed_section_ids: list[Any] = []
    completed_step_keys: list[Any] = []
    item_results: Optional[dict[str, Any]] = None
    percent: int = 0
    completed: bool = False
    completed_at: Optional[datetime] = None
    cards_added: int = 0

    class Config:
        from_attributes = True


class LessonProgressUpdate(BaseModel):
    completed_section_ids: Optional[list[int]] = None
    completed_step_keys: Optional[list[str]] = None
    item_results: Optional[dict[str, Any]] = None
    completed: Optional[bool] = None
    push_to_fsrs: bool = True


class PaginatedCourses(BaseModel):
    items: list[CourseOut]
    total: int
    page: int
    page_size: int


class PaginatedLessons(BaseModel):
    items: list[LessonOut]
    total: int
    page: int
    page_size: int
