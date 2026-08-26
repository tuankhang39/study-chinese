"""Curriculum (Giáo trình) admin + learner APIs — step-based player."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import joinedload

from app.deps import AdminUser, CurrentUser, DbSession
from app.models import (
    Course,
    Lesson,
    LessonItem,
    LessonProgress,
    LessonSection,
    LessonStep,
    LessonVocab,
    Vocabulary,
)
from app.schemas import (
    CourseCreate,
    CourseOut,
    CourseUpdate,
    LessonCreate,
    LessonDetailOut,
    LessonItemCreate,
    LessonItemOut,
    LessonItemUpdate,
    LessonOut,
    LessonPlayerOut,
    LessonProgressOut,
    LessonProgressUpdate,
    LessonSectionCreate,
    LessonSectionOut,
    LessonSectionUpdate,
    LessonStepCreate,
    LessonStepOut,
    LessonStepUpdate,
    LessonUpdate,
    PaginatedCourses,
    PaginatedLessons,
)
from app.services.fsrs_service import ensure_cards_for_vocab_ids
from app.services.lesson_parse import items_from_lesson_draft
from app.services.lesson_templates import (
    LESSON_TYPES,
    lesson_type_for_hsk1,
    pipeline_for_type,
)
from app.services.pinyin_util import ensure_pinyin, has_hanzi

router = APIRouter(tags=["curriculum"])

SECTION_TYPES = {
    "objectives",
    "tongue_twister",
    "warmup",
    "text",
    "vocab",
    "grammar",
    "tip",
    "exercise",
    "activity",
    "bonus",
    "summary",
    "other",
}

ITEM_TYPES = {
    "vocab_card",
    "sentence_card",
    "dialogue_line",
    "grammar_tip",
    "quiz_prompt",
    "media",
    "objective",
}


def _data_root() -> Path:
    candidates: list[Path] = [Path("/app/data"), Path.cwd() / "data"]
    try:
        here = Path(__file__).resolve()
        for i in (4, 3, 2):
            if len(here.parents) > i:
                candidates.append(here.parents[i] / "data")
    except Exception:
        pass
    for p in candidates:
        if p.exists():
            return p
    root = Path.cwd() / "data"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _media_curriculum() -> Path:
    p = _data_root() / "curriculum"
    p.mkdir(parents=True, exist_ok=True)
    (p / "uploads").mkdir(parents=True, exist_ok=True)
    return p


def _course_out(c: Course, lesson_count: int = 0, progress_percent: int | None = None) -> CourseOut:
    return CourseOut(
        id=c.id,
        slug=c.slug,
        title=c.title,
        title_en=c.title_en,
        description=c.description or "",
        hsk_level=c.hsk_level,
        cover_image_url=c.cover_image_url,
        published=c.published,
        coming_soon=bool(getattr(c, "coming_soon", False)),
        sort_order=c.sort_order,
        lesson_count=lesson_count,
        progress_percent=progress_percent,
    )


def _item_out(it: LessonItem) -> LessonItemOut:
    data = LessonItemOut.model_validate(it)
    if has_hanzi(data.hanzi):
        py = ensure_pinyin(data.hanzi, data.pinyin)
        if py and py != data.pinyin:
            data = data.model_copy(update={"pinyin": py})
    return data


def _step_out(step: LessonStep, include_items: bool = True) -> LessonStepOut:
    items = []
    if include_items and step.items is not None:
        items = [_item_out(i) for i in sorted(step.items, key=lambda x: x.sort_order)]
    return LessonStepOut(
        id=step.id,
        lesson_id=step.lesson_id,
        step_key=step.step_key,
        title_vi=step.title_vi,
        sort_order=step.sort_order,
        required=step.required,
        items=items,
    )


def _lesson_out(
    lesson: Lesson,
    *,
    include_sections: bool = False,
    include_steps: bool = False,
    locked: bool = False,
    progress_percent: int | None = None,
) -> LessonOut | LessonDetailOut:
    base = LessonOut(
        id=lesson.id,
        course_id=lesson.course_id,
        number=lesson.number,
        title_zh=lesson.title_zh,
        title_vi=lesson.title_vi,
        title_en=lesson.title_en,
        title_pinyin=ensure_pinyin(lesson.title_zh),
        lesson_type=getattr(lesson, "lesson_type", None) or "dialogue_core",
        estimated_minutes=getattr(lesson, "estimated_minutes", None) or 12,
        unlock_rule=getattr(lesson, "unlock_rule", None) or "sequential",
        objectives=lesson.objectives,
        grammar_points=lesson.grammar_points,
        page_start=lesson.page_start,
        page_end=lesson.page_end,
        cover_image_url=lesson.cover_image_url,
        published=lesson.published,
        section_count=len(lesson.sections) if lesson.sections is not None else 0,
        step_count=len(lesson.steps) if getattr(lesson, "steps", None) is not None else 0,
        locked=locked,
        progress_percent=progress_percent,
    )
    if include_sections or include_steps:
        return LessonDetailOut(
            **base.model_dump(),
            sections=[
                LessonSectionOut.model_validate(s)
                for s in sorted(lesson.sections or [], key=lambda x: x.sort_order)
            ]
            if include_sections
            else [],
            steps=[_step_out(s) for s in sorted(lesson.steps or [], key=lambda x: x.sort_order)]
            if include_steps
            else [],
        )
    return base


def _progress_out(row: LessonProgress | None, lesson_id: int, cards_added: int = 0) -> LessonProgressOut:
    if not row:
        return LessonProgressOut(lesson_id=lesson_id, cards_added=cards_added)
    return LessonProgressOut(
        lesson_id=row.lesson_id,
        completed_section_ids=row.completed_section_ids or [],
        completed_step_keys=getattr(row, "completed_step_keys", None) or [],
        item_results=getattr(row, "item_results", None),
        percent=row.percent or 0,
        completed=bool(row.completed),
        completed_at=getattr(row, "completed_at", None),
        cards_added=cards_added,
    )


def _ensure_steps(db: DbSession, lesson: Lesson) -> list[LessonStep]:
    existing = (
        db.query(LessonStep).filter(LessonStep.lesson_id == lesson.id).order_by(LessonStep.sort_order).all()
    )
    if existing:
        return existing
    pipe = pipeline_for_type(lesson.lesson_type or "dialogue_core", lesson.number)
    created = []
    for s in pipe:
        step = LessonStep(
            lesson_id=lesson.id,
            step_key=s["step_key"],
            title_vi=s["title_vi"],
            sort_order=s["sort_order"],
            required=s["required"],
        )
        db.add(step)
        created.append(step)
    db.flush()
    return created


def _is_lesson_locked(db: DbSession, user_id: int | None, lesson: Lesson, course_lessons: list[Lesson]) -> bool:
    if (lesson.unlock_rule or "sequential") != "sequential":
        return False
    if user_id is None:
        return lesson.number > 1
    prev = [L for L in course_lessons if L.number < lesson.number]
    if not prev:
        return False
    prev_ids = [L.id for L in prev]
    done = {
        r.lesson_id
        for r in db.query(LessonProgress)
        .filter(
            LessonProgress.user_id == user_id,
            LessonProgress.lesson_id.in_(prev_ids),
            LessonProgress.completed.is_(True),
        )
        .all()
    }
    # unlock if previous lesson completed
    immediate_prev = max(prev, key=lambda L: L.number)
    return immediate_prev.id not in done


# ---- Public / learner ----


@router.get("/curriculum/courses", response_model=list[CourseOut])
def list_courses(db: DbSession) -> list[CourseOut]:
    """List HSK catalog (published or coming_soon shells)."""
    rows = db.query(Course).order_by(Course.sort_order, Course.hsk_level, Course.id).all()
    out = []
    for c in rows:
        if not c.published and not getattr(c, "coming_soon", False):
            continue
        n = db.query(Lesson).filter(Lesson.course_id == c.id, Lesson.published.is_(True)).count()
        out.append(_course_out(c, lesson_count=n))
    return out


@router.get("/curriculum/catalog", response_model=list[CourseOut])
def catalog(user: CurrentUser, db: DbSession) -> list[CourseOut]:
    rows = db.query(Course).order_by(Course.sort_order, Course.hsk_level).all()
    out = []
    for c in rows:
        if not c.published and not c.coming_soon:
            continue
        lessons = (
            db.query(Lesson).filter(Lesson.course_id == c.id, Lesson.published.is_(True)).all()
        )
        pct = 0
        if lessons:
            ids = [L.id for L in lessons]
            done = (
                db.query(LessonProgress)
                .filter(
                    LessonProgress.user_id == user.id,
                    LessonProgress.lesson_id.in_(ids),
                    LessonProgress.completed.is_(True),
                )
                .count()
            )
            pct = int(round(100 * done / len(lessons)))
        out.append(_course_out(c, lesson_count=len(lessons), progress_percent=pct))
    return out


@router.get("/curriculum/courses/{slug}", response_model=CourseOut)
def get_course(slug: str, db: DbSession) -> CourseOut:
    c = db.query(Course).filter(Course.slug == slug).first()
    if not c or (not c.published and not c.coming_soon):
        raise HTTPException(404, "Course not found")
    n = db.query(Lesson).filter(Lesson.course_id == c.id).count()
    return _course_out(c, lesson_count=n)


@router.get("/curriculum/courses/{slug}/lessons", response_model=list[LessonOut])
def list_course_lessons(slug: str, user: CurrentUser, db: DbSession) -> list[LessonOut]:
    c = db.query(Course).filter(Course.slug == slug).first()
    if not c or (not c.published and not c.coming_soon):
        raise HTTPException(404, "Course not found")
    if c.coming_soon and not c.published:
        return []
    lessons = (
        db.query(Lesson)
        .options(joinedload(Lesson.sections), joinedload(Lesson.steps))
        .filter(Lesson.course_id == c.id, Lesson.published.is_(True))
        .order_by(Lesson.number)
        .all()
    )
    prog = {
        r.lesson_id: r
        for r in db.query(LessonProgress)
        .filter(LessonProgress.user_id == user.id, LessonProgress.lesson_id.in_([L.id for L in lessons] or [0]))
        .all()
    }
    out = []
    for L in lessons:
        locked = _is_lesson_locked(db, user.id, L, lessons)
        p = prog.get(L.id)
        out.append(
            _lesson_out(
                L,
                locked=locked,
                progress_percent=p.percent if p else 0,
            )
        )
    return out  # type: ignore[return-value]


@router.get("/curriculum/lessons/{lesson_id}", response_model=LessonDetailOut)
def get_lesson(lesson_id: int, db: DbSession) -> LessonDetailOut:
    lesson = (
        db.query(Lesson)
        .options(
            joinedload(Lesson.sections),
            joinedload(Lesson.steps).joinedload(LessonStep.items),
        )
        .filter(Lesson.id == lesson_id)
        .first()
    )
    if not lesson or not lesson.published:
        raise HTTPException(404, "Lesson not found")
    return _lesson_out(lesson, include_sections=True, include_steps=True)  # type: ignore[return-value]


@router.get("/curriculum/lessons/{lesson_id}/player", response_model=LessonPlayerOut)
def get_lesson_player(lesson_id: int, user: CurrentUser, db: DbSession) -> LessonPlayerOut:
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.steps).joinedload(LessonStep.items))
        .filter(Lesson.id == lesson_id)
        .first()
    )
    if not lesson or not lesson.published:
        raise HTTPException(404, "Lesson not found")
    siblings = (
        db.query(Lesson)
        .filter(Lesson.course_id == lesson.course_id, Lesson.published.is_(True))
        .order_by(Lesson.number)
        .all()
    )
    if _is_lesson_locked(db, user.id, lesson, siblings):
        raise HTTPException(403, "Hoàn thành bài trước để mở khóa")
    _ensure_steps(db, lesson)
    db.commit()
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.steps).joinedload(LessonStep.items))
        .filter(Lesson.id == lesson_id)
        .first()
    )
    assert lesson
    prog = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    next_id = None
    for L in siblings:
        if L.number > lesson.number:
            next_id = L.id
            break
    pages = []
    if lesson.page_start and lesson.page_end:
        for p in range(lesson.page_start, min(lesson.page_end, lesson.page_start + 5) + 1):
            pages.append(f"/api/media/curriculum/hsk1/pages/page_{p:03d}.jpg")
    return LessonPlayerOut(
        lesson=_lesson_out(lesson),  # type: ignore[arg-type]
        steps=[_step_out(s) for s in sorted(lesson.steps, key=lambda x: x.sort_order)],
        progress=_progress_out(prog, lesson_id),
        next_lesson_id=next_id,
        source_pages=pages,
    )


@router.get("/curriculum/lessons/{lesson_id}/progress", response_model=LessonProgressOut)
def get_progress(lesson_id: int, user: CurrentUser, db: DbSession) -> LessonProgressOut:
    row = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    return _progress_out(row, lesson_id)


@router.post("/curriculum/lessons/{lesson_id}/progress", response_model=LessonProgressOut)
def update_progress(
    lesson_id: int, body: LessonProgressUpdate, user: CurrentUser, db: DbSession
) -> LessonProgressOut:
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.steps), joinedload(Lesson.vocab_links))
        .filter(Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    row = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == user.id, LessonProgress.lesson_id == lesson_id)
        .first()
    )
    if not row:
        row = LessonProgress(user_id=user.id, lesson_id=lesson_id)
        db.add(row)

    if body.completed_section_ids is not None:
        row.completed_section_ids = list(dict.fromkeys(body.completed_section_ids))
    if body.completed_step_keys is not None:
        row.completed_step_keys = list(dict.fromkeys(body.completed_step_keys))
    if body.item_results is not None:
        row.item_results = body.item_results

    required = [s.step_key for s in (lesson.steps or []) if s.required]
    done_keys = set(row.completed_step_keys or [])
    if required:
        percent = int(round(100 * len(done_keys & set(required)) / len(required)))
    else:
        percent = 100 if body.completed else (row.percent or 0)
    completed = body.completed is True or (required and set(required).issubset(done_keys))
    if completed:
        percent = 100
        if not row.completed_at:
            row.completed_at = datetime.now(timezone.utc)
    row.percent = min(100, percent)
    row.completed = completed
    db.commit()
    db.refresh(row)

    cards_added = 0
    if completed and body.push_to_fsrs:
        vids = [lv.vocab_id for lv in (lesson.vocab_links or [])]
        if not vids:
            # fallback: match vocab_card hanzi
            items = (
                db.query(LessonItem)
                .filter(LessonItem.lesson_id == lesson_id, LessonItem.item_type == "vocab_card")
                .all()
            )
            hanzi_set = {i.hanzi for i in items if i.hanzi}
            if hanzi_set:
                vids = [
                    v.id
                    for v in db.query(Vocabulary).filter(Vocabulary.hanzi.in_(hanzi_set)).all()
                ]
        cards_added = ensure_cards_for_vocab_ids(db, user.id, vids)

    return _progress_out(row, lesson_id, cards_added=cards_added)


# ---- Media ----


@router.get("/media/curriculum/{path:path}")
def serve_curriculum_media(path: str) -> FileResponse:
    root = _media_curriculum().resolve()
    target = (root / path).resolve()
    if not str(target).startswith(str(root)) or not target.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(target)


@router.post("/admin/curriculum/upload")
async def upload_section_image(_: AdminUser, file: UploadFile = File(...)) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "Chỉ nhận file ảnh")
    ext = Path(file.filename or "img.jpg").suffix.lower() or ".jpg"
    if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
        ext = ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    dest = _media_curriculum() / "uploads" / name
    data = await file.read()
    if len(data) > 8 * 1024 * 1024:
        raise HTTPException(400, "Ảnh tối đa 8MB")
    dest.write_bytes(data)
    return {"image_url": f"/api/media/curriculum/uploads/{name}"}


# ---- Admin CRUD courses/lessons/sections/steps/items ----


@router.get("/admin/curriculum/courses", response_model=PaginatedCourses)
def admin_list_courses(
    _: AdminUser,
    db: DbSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedCourses:
    q = db.query(Course)
    total = q.count()
    items = q.order_by(Course.sort_order, Course.id).offset((page - 1) * page_size).limit(page_size).all()
    outs = []
    for c in items:
        n = db.query(Lesson).filter(Lesson.course_id == c.id).count()
        outs.append(_course_out(c, lesson_count=n))
    return PaginatedCourses(items=outs, total=total, page=page, page_size=page_size)


@router.post("/admin/curriculum/courses", response_model=CourseOut)
def admin_create_course(_: AdminUser, body: CourseCreate, db: DbSession) -> CourseOut:
    if db.query(Course).filter(Course.slug == body.slug).first():
        raise HTTPException(400, "Slug đã tồn tại")
    c = Course(**body.model_dump())
    db.add(c)
    db.commit()
    db.refresh(c)
    return _course_out(c)


@router.patch("/admin/curriculum/courses/{course_id}", response_model=CourseOut)
def admin_update_course(_: AdminUser, course_id: int, body: CourseUpdate, db: DbSession) -> CourseOut:
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    db.commit()
    db.refresh(c)
    return _course_out(c)


@router.delete("/admin/curriculum/courses/{course_id}")
def admin_delete_course(_: AdminUser, course_id: int, db: DbSession) -> dict[str, bool]:
    c = db.query(Course).filter(Course.id == course_id).first()
    if not c:
        raise HTTPException(404, "Not found")
    db.delete(c)
    db.commit()
    return {"ok": True}


@router.get("/admin/curriculum/lessons", response_model=PaginatedLessons)
def admin_list_lessons(
    _: AdminUser,
    db: DbSession,
    course_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginatedLessons:
    q = db.query(Lesson).options(joinedload(Lesson.sections), joinedload(Lesson.steps))
    if course_id:
        q = q.filter(Lesson.course_id == course_id)
    total = q.count()
    items = q.order_by(Lesson.course_id, Lesson.number).offset((page - 1) * page_size).limit(page_size).all()
    return PaginatedLessons(
        items=[_lesson_out(L) for L in items],  # type: ignore[misc]
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/admin/curriculum/lessons", response_model=LessonDetailOut)
def admin_create_lesson(_: AdminUser, body: LessonCreate, db: DbSession) -> LessonDetailOut:
    if not db.query(Course).filter(Course.id == body.course_id).first():
        raise HTTPException(400, "Course không tồn tại")
    if body.lesson_type not in LESSON_TYPES:
        raise HTTPException(400, f"lesson_type phải thuộc {sorted(LESSON_TYPES)}")
    lesson = Lesson(**body.model_dump())
    db.add(lesson)
    db.flush()
    _ensure_steps(db, lesson)
    db.commit()
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.sections), joinedload(Lesson.steps).joinedload(LessonStep.items))
        .filter(Lesson.id == lesson.id)
        .first()
    )
    assert lesson
    return _lesson_out(lesson, include_sections=True, include_steps=True)  # type: ignore[return-value]


@router.get("/admin/curriculum/lessons/{lesson_id}", response_model=LessonDetailOut)
def admin_get_lesson(_: AdminUser, lesson_id: int, db: DbSession) -> LessonDetailOut:
    lesson = (
        db.query(Lesson)
        .options(
            joinedload(Lesson.sections),
            joinedload(Lesson.steps).joinedload(LessonStep.items),
        )
        .filter(Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(404, "Not found")
    return _lesson_out(lesson, include_sections=True, include_steps=True)  # type: ignore[return-value]


@router.patch("/admin/curriculum/lessons/{lesson_id}", response_model=LessonDetailOut)
def admin_update_lesson(
    _: AdminUser, lesson_id: int, body: LessonUpdate, db: DbSession
) -> LessonDetailOut:
    lesson = (
        db.query(Lesson)
        .options(joinedload(Lesson.sections), joinedload(Lesson.steps).joinedload(LessonStep.items))
        .filter(Lesson.id == lesson_id)
        .first()
    )
    if not lesson:
        raise HTTPException(404, "Not found")
    data = body.model_dump(exclude_unset=True)
    if "lesson_type" in data and data["lesson_type"] not in LESSON_TYPES:
        raise HTTPException(400, f"lesson_type phải thuộc {sorted(LESSON_TYPES)}")
    for k, v in data.items():
        setattr(lesson, k, v)
    db.commit()
    db.refresh(lesson)
    return _lesson_out(lesson, include_sections=True, include_steps=True)  # type: ignore[return-value]


@router.delete("/admin/curriculum/lessons/{lesson_id}")
def admin_delete_lesson(_: AdminUser, lesson_id: int, db: DbSession) -> dict[str, bool]:
    lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(404, "Not found")
    db.delete(lesson)
    db.commit()
    return {"ok": True}


@router.post("/admin/curriculum/sections", response_model=LessonSectionOut)
def admin_create_section(_: AdminUser, body: LessonSectionCreate, db: DbSession) -> LessonSectionOut:
    if body.section_type not in SECTION_TYPES:
        raise HTTPException(400, f"section_type phải thuộc {sorted(SECTION_TYPES)}")
    if not db.query(Lesson).filter(Lesson.id == body.lesson_id).first():
        raise HTTPException(400, "Lesson không tồn tại")
    s = LessonSection(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return LessonSectionOut.model_validate(s)


@router.patch("/admin/curriculum/sections/{section_id}", response_model=LessonSectionOut)
def admin_update_section(
    _: AdminUser, section_id: int, body: LessonSectionUpdate, db: DbSession
) -> LessonSectionOut:
    s = db.query(LessonSection).filter(LessonSection.id == section_id).first()
    if not s:
        raise HTTPException(404, "Not found")
    data = body.model_dump(exclude_unset=True)
    if "section_type" in data and data["section_type"] not in SECTION_TYPES:
        raise HTTPException(400, f"section_type phải thuộc {sorted(SECTION_TYPES)}")
    for k, v in data.items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return LessonSectionOut.model_validate(s)


@router.delete("/admin/curriculum/sections/{section_id}")
def admin_delete_section(_: AdminUser, section_id: int, db: DbSession) -> dict[str, bool]:
    s = db.query(LessonSection).filter(LessonSection.id == section_id).first()
    if not s:
        raise HTTPException(404, "Not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/admin/curriculum/steps", response_model=LessonStepOut)
def admin_create_step(_: AdminUser, body: LessonStepCreate, db: DbSession) -> LessonStepOut:
    if not db.query(Lesson).filter(Lesson.id == body.lesson_id).first():
        raise HTTPException(400, "Lesson không tồn tại")
    s = LessonStep(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _step_out(s, include_items=False)


@router.patch("/admin/curriculum/steps/{step_id}", response_model=LessonStepOut)
def admin_update_step(_: AdminUser, step_id: int, body: LessonStepUpdate, db: DbSession) -> LessonStepOut:
    s = db.query(LessonStep).options(joinedload(LessonStep.items)).filter(LessonStep.id == step_id).first()
    if not s:
        raise HTTPException(404, "Not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return _step_out(s)


@router.delete("/admin/curriculum/steps/{step_id}")
def admin_delete_step(_: AdminUser, step_id: int, db: DbSession) -> dict[str, bool]:
    s = db.query(LessonStep).filter(LessonStep.id == step_id).first()
    if not s:
        raise HTTPException(404, "Not found")
    db.delete(s)
    db.commit()
    return {"ok": True}


@router.post("/admin/curriculum/items", response_model=LessonItemOut)
def admin_create_item(_: AdminUser, body: LessonItemCreate, db: DbSession) -> LessonItemOut:
    if body.item_type not in ITEM_TYPES:
        raise HTTPException(400, f"item_type phải thuộc {sorted(ITEM_TYPES)}")
    if not db.query(Lesson).filter(Lesson.id == body.lesson_id).first():
        raise HTTPException(400, "Lesson không tồn tại")
    it = LessonItem(**body.model_dump())
    if has_hanzi(it.hanzi):
        it.pinyin = ensure_pinyin(it.hanzi, it.pinyin)
    db.add(it)
    db.commit()
    db.refresh(it)
    return _item_out(it)


@router.patch("/admin/curriculum/items/{item_id}", response_model=LessonItemOut)
def admin_update_item(_: AdminUser, item_id: int, body: LessonItemUpdate, db: DbSession) -> LessonItemOut:
    it = db.query(LessonItem).filter(LessonItem.id == item_id).first()
    if not it:
        raise HTTPException(404, "Not found")
    data = body.model_dump(exclude_unset=True)
    if "item_type" in data and data["item_type"] not in ITEM_TYPES:
        raise HTTPException(400, f"item_type phải thuộc {sorted(ITEM_TYPES)}")
    for k, v in data.items():
        setattr(it, k, v)
    if has_hanzi(it.hanzi):
        it.pinyin = ensure_pinyin(it.hanzi, it.pinyin)
    db.commit()
    db.refresh(it)
    return _item_out(it)


@router.delete("/admin/curriculum/items/{item_id}")
def admin_delete_item(_: AdminUser, item_id: int, db: DbSession) -> dict[str, bool]:
    it = db.query(LessonItem).filter(LessonItem.id == item_id).first()
    if not it:
        raise HTTPException(404, "Not found")
    db.delete(it)
    db.commit()
    return {"ok": True}


def _map_vocab_links(db: DbSession, lesson_id: int, vocab_items: list[dict]) -> int:
    linked = 0
    for i, v in enumerate(vocab_items):
        hanzi = v.get("hanzi")
        if not hanzi:
            continue
        vocab = db.query(Vocabulary).filter(Vocabulary.hanzi == hanzi).first()
        if not vocab:
            continue
        exists = (
            db.query(LessonVocab)
            .filter(LessonVocab.lesson_id == lesson_id, LessonVocab.vocab_id == vocab.id)
            .first()
        )
        if exists:
            continue
        db.add(LessonVocab(lesson_id=lesson_id, vocab_id=vocab.id, is_key=True, sort_order=i))
        # enrich item meaning from bank if missing
        linked += 1
    return linked


def _seed_hsk_shells(db: DbSession) -> None:
    """Ensure HSK2–6 coming-soon course shells exist (HSK1 comes from full seed)."""
    for level in range(2, 7):
        slug = f"hsk{level}"
        if db.query(Course).filter(Course.slug == slug).first():
            continue
        db.add(
            Course(
                slug=slug,
                title=f"HSK {level}",
                title_en=f"HSK Level {level}",
                description=f"Khóa HSK {level} — sắp mở",
                hsk_level=level,
                published=False,
                coming_soon=True,
                sort_order=level,
            )
        )
    db.flush()


@router.post("/admin/curriculum/seed-hsk1")
def admin_seed_hsk1(_: AdminUser, db: DbSession, replace: bool = False) -> dict:
    """Seed HSK1 with structured steps/items from OCR draft + HSK2-6 shells."""
    root = _data_root()
    toc_path = root / "curriculum" / "hsk1" / "toc_map.json"
    draft_path = root / "curriculum" / "hsk1" / "lessons_draft.json"
    if not toc_path.exists():
        raise HTTPException(404, f"Missing {toc_path}")
    toc = json.loads(toc_path.read_text(encoding="utf-8"))
    draft_by_num: dict[int, dict] = {}
    if draft_path.exists():
        draft = json.loads(draft_path.read_text(encoding="utf-8"))
        for L in draft.get("lessons") or []:
            draft_by_num[int(L["number"])] = L

    _seed_hsk_shells(db)

    existing = db.query(Course).filter(Course.slug == "hsk1").first()
    if existing and not replace:
        # still ensure shells
        db.commit()
        return {"ok": True, "course_id": existing.id, "message": "Already seeded (pass replace=true)"}
    if existing and replace:
        lesson_ids = [r[0] for r in db.query(Lesson.id).filter(Lesson.course_id == existing.id).all()]
        if lesson_ids:
            db.query(LessonProgress).filter(LessonProgress.lesson_id.in_(lesson_ids)).delete(
                synchronize_session=False
            )
            db.query(LessonVocab).filter(LessonVocab.lesson_id.in_(lesson_ids)).delete(
                synchronize_session=False
            )
            db.query(LessonItem).filter(LessonItem.lesson_id.in_(lesson_ids)).delete(
                synchronize_session=False
            )
            db.query(LessonStep).filter(LessonStep.lesson_id.in_(lesson_ids)).delete(
                synchronize_session=False
            )
            db.query(LessonSection).filter(LessonSection.lesson_id.in_(lesson_ids)).delete(
                synchronize_session=False
            )
            db.query(Lesson).filter(Lesson.id.in_(lesson_ids)).delete(synchronize_session=False)
        db.delete(existing)
        db.commit()
        _seed_hsk_shells(db)

    course = Course(
        slug="hsk1",
        title=toc["book"]["title_zh"],
        title_en=toc["book"]["title_en"],
        description=(
            f"15 bài · ~{toc['book']['vocab_target']} từ · {toc['book']['language_points']} điểm ngữ pháp · "
            f"{toc['book']['recommended_hours']} giờ"
        ),
        hsk_level=1,
        cover_image_url="/api/media/curriculum/hsk1/pages/page_015.jpg",
        published=True,
        coming_soon=False,
        sort_order=1,
    )
    db.add(course)
    db.flush()

    total_items = 0
    total_vocab_links = 0

    for meta in toc["lessons"]:
        num = int(meta["number"])
        draft_L = draft_by_num.get(num) or {}
        page_start = draft_L.get("page_start") or meta.get("pdf_page_approx")
        page_end = draft_L.get("page_end")
        cover = (
            f"/api/media/curriculum/hsk1/pages/page_{int(page_start):03d}.jpg" if page_start else None
        )
        ltype = lesson_type_for_hsk1(num)
        lesson = Lesson(
            course_id=course.id,
            number=num,
            title_zh=meta["title_zh"],
            title_en=meta.get("title_en"),
            lesson_type=ltype,
            estimated_minutes=12,
            unlock_rule="sequential",
            objectives=None,
            grammar_points=meta.get("grammar") or [],
            page_start=page_start,
            page_end=page_end,
            cover_image_url=cover,
            published=True,
        )
        db.add(lesson)
        db.flush()

        # keep raw sections for admin reference
        for i, sec in enumerate(draft_L.get("sections") or []):
            page = sec.get("page")
            db.add(
                LessonSection(
                    lesson_id=lesson.id,
                    sort_order=i,
                    section_type=sec.get("type") or "other",
                    title=(sec.get("title") or "")[:240],
                    content=sec.get("content") or "",
                    image_url=f"/api/media/curriculum/hsk1/pages/page_{int(page):03d}.jpg" if page else cover,
                    page_ref=page,
                )
            )

        steps_meta = pipeline_for_type(ltype, num)
        step_by_key: dict[str, LessonStep] = {}
        for sm in steps_meta:
            st = LessonStep(
                lesson_id=lesson.id,
                step_key=sm["step_key"],
                title_vi=sm["title_vi"],
                sort_order=sm["sort_order"],
                required=sm["required"],
            )
            db.add(st)
            db.flush()
            step_by_key[sm["step_key"]] = st

        grouped = items_from_lesson_draft({**draft_L, "grammar_points": meta.get("grammar") or []})
        for step_key, items in grouped.items():
            step = step_by_key.get(step_key)
            if not step:
                continue
            for it in items:
                # enrich meaning from vocab bank
                meaning_vi = it.get("meaning_vi")
                if it.get("hanzi") and not meaning_vi:
                    vb = db.query(Vocabulary).filter(Vocabulary.hanzi == it["hanzi"]).first()
                    if vb:
                        meaning_vi = vb.meaning_vi
                        if not it.get("pinyin"):
                            it["pinyin"] = vb.pinyin
                        if not it.get("meaning_en"):
                            it["meaning_en"] = vb.meaning_en
                db.add(
                    LessonItem(
                        lesson_id=lesson.id,
                        step_id=step.id,
                        sort_order=it.get("sort_order", 0),
                        item_type=it.get("item_type") or "vocab_card",
                        hanzi=it.get("hanzi"),
                        pinyin=ensure_pinyin(it.get("hanzi"), it.get("pinyin")),
                        meaning_vi=meaning_vi,
                        meaning_en=it.get("meaning_en"),
                        audio_text=it.get("audio_text") or it.get("hanzi"),
                        speaker=it.get("speaker"),
                        image_url=it.get("image_url"),
                        source_page=it.get("source_page") or page_start,
                        meta=it.get("meta"),
                    )
                )
                total_items += 1

        total_vocab_links += _map_vocab_links(db, lesson.id, grouped.get("vocab") or [])

        # complete step: media tip pointing to source pages
        if "complete" in step_by_key:
            db.add(
                LessonItem(
                    lesson_id=lesson.id,
                    step_id=step_by_key["complete"].id,
                    sort_order=0,
                    item_type="media",
                    meaning_vi="Bạn đã hoàn thành các bước chính. Ôn flashcard để nhớ lâu.",
                    image_url=cover,
                    source_page=page_start,
                )
            )
            total_items += 1

    db.commit()
    n_lessons = db.query(Lesson).filter(Lesson.course_id == course.id).count()
    n_steps = db.query(LessonStep).join(Lesson).filter(Lesson.course_id == course.id).count()
    return {
        "ok": True,
        "course_id": course.id,
        "lessons": n_lessons,
        "steps": n_steps,
        "items": total_items,
        "vocab_links": total_vocab_links,
        "ocr_draft_used": bool(draft_by_num),
    }
