#!/usr/bin/env python3
"""Pre-HSK course: Phát âm nền (thanh mẫu / vận mẫu / thanh điệu).

Creates course slug=pinyin (sort_order=0), moves any legacy single phonics
lesson out of HSK1 (renumbering HSK1 back to 1..N), then rebuilds the pinyin
course as 5 bite-sized lessons instead of one giant lesson:

  1. Nhập môn & Mẹo phát âm      — structure, tongue/mouth/breath tips
  2. Thanh mẫu dễ (Môi–Lưỡi–Gốc) — b p m f / d t n l / g k h
  3. Thanh mẫu khó (3 nhóm lưỡi) — j q x / zh ch sh r / z c s
  4. Vận mẫu & Ghép âm           — a o e i u ü, ai ei ao ou, an ang en eng…
  5. Thanh điệu & Ôn tập tổng    — 4 tones, sandhi, full quiz, review

Idempotent: safe to re-run; wipes and rebuilds only the pinyin course's lessons.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models import Course, Lesson, LessonItem, LessonProgress, LessonStep
from app.services.lesson_templates import pipeline_for_type
from app.services.pinyin_util import ensure_pinyin

PINYIN_SLUG = "pinyin"
HSK1_SLUG = "hsk1"


def ensure_pinyin_course(db) -> Course:
    course = db.query(Course).filter(Course.slug == PINYIN_SLUG).first()
    desc = (
        "Học trước HSK 1 — thanh mẫu, vận mẫu, thanh điệu: mẹo lưỡi, khuôn miệng, "
        "bật hơi, và luyện ghép âm. Chia làm 5 bài ngắn, học từng phần cho dễ nhớ."
    )
    if course:
        course.title = "Phát âm nền"
        course.title_en = "Pinyin Foundations"
        course.description = desc
        course.hsk_level = 0
        course.published = True
        course.coming_soon = False
        course.sort_order = 0
        db.flush()
        return course
    course = Course(
        slug=PINYIN_SLUG,
        title="Phát âm nền",
        title_en="Pinyin Foundations",
        description=desc,
        hsk_level=0,
        published=True,
        coming_soon=False,
        sort_order=0,
    )
    db.add(course)
    db.flush()
    return course


def renumber_hsk1_down(db, hsk1_id: int) -> int:
    """After removing the legacy phonics lesson, shift remaining numbers down by 1."""
    lessons = (
        db.query(Lesson)
        .filter(Lesson.course_id == hsk1_id)
        .order_by(Lesson.number)
        .all()
    )
    if not lessons:
        return 0
    for L in lessons:
        L.number = L.number + 1000
    db.flush()
    for i, L in enumerate(sorted(lessons, key=lambda x: x.number), start=1):
        L.number = i
    db.flush()
    return len(lessons)


def migrate_legacy_single_lesson(db, pinyin: Course, hsk1: Course | None) -> None:
    """One-time cleanup: move any phonics lesson still sitting in HSK1, and
    wipe any old single-lesson pinyin course content so we can rebuild as 5."""
    if hsk1:
        stray = (
            db.query(Lesson)
            .filter(Lesson.course_id == hsk1.id, Lesson.lesson_type == "phonics_focus")
            .first()
        )
        if stray:
            print(f"Moving stray HSK1 phonics lesson id={stray.id} -> deleting (superseded by pinyin course)")
            db.query(LessonProgress).filter(LessonProgress.lesson_id == stray.id).delete()
            db.query(LessonItem).filter(LessonItem.lesson_id == stray.id).delete()
            for st in list(stray.steps or []):
                db.delete(st)
            db.delete(stray)
            db.flush()
            n = renumber_hsk1_down(db, hsk1.id)
            print(f"Renumbered HSK1 -> {n} lessons (1-{n})")

    # Wipe all existing pinyin lessons so we can rebuild cleanly as 5.
    old_lessons = db.query(Lesson).filter(Lesson.course_id == pinyin.id).all()
    for L in old_lessons:
        db.query(LessonProgress).filter(LessonProgress.lesson_id == L.id).delete()
        db.query(LessonItem).filter(LessonItem.lesson_id == L.id).delete()
        for st in list(L.steps or []):
            db.delete(st)
        db.delete(L)
    db.flush()


def add_item(
    db,
    *,
    lesson_id: int,
    step_id: int,
    sort_order: int,
    item_type: str,
    hanzi: str | None = None,
    pinyin: str | None = None,
    meaning_vi: str | None = None,
    meaning_en: str | None = None,
    audio_text: str | None = None,
    speaker: str | None = None,
    meta: dict | None = None,
) -> None:
    py = ensure_pinyin(hanzi, pinyin) if hanzi else pinyin
    db.add(
        LessonItem(
            lesson_id=lesson_id,
            step_id=step_id,
            sort_order=sort_order,
            item_type=item_type,
            hanzi=hanzi,
            pinyin=py,
            meaning_vi=meaning_vi,
            meaning_en=meaning_en,
            audio_text=audio_text or hanzi,
            speaker=speaker,
            meta=meta,
        )
    )


def build_steps(db, lesson: Lesson, titles: dict[str, str]) -> dict[str, LessonStep]:
    """Create the phonics_focus pipeline for one lesson, with per-lesson titles.

    NOTE: pipeline_for_type() is called WITHOUT a lesson_number so the HSK1-only
    HSK1_EXTRA_STEPS (tongue_twister injection for numbers 2/3) never fires here.
    """
    pipe = pipeline_for_type("phonics_focus")
    steps: dict[str, LessonStep] = {}
    for sm in pipe:
        title = titles.get(sm["step_key"], sm["title_vi"])
        st = LessonStep(
            lesson_id=lesson.id,
            step_key=sm["step_key"],
            title_vi=title,
            sort_order=sm["sort_order"],
            required=sm["required"],
        )
        db.add(st)
        db.flush()
        steps[sm["step_key"]] = st
    return steps


def make_lesson(db, course: Course, number: int, title_zh: str, title_vi: str, minutes: int) -> Lesson:
    lesson = Lesson(
        course_id=course.id,
        number=number,
        title_zh=title_zh,
        title_vi=title_vi,
        title_en=None,
        lesson_type="phonics_focus",
        estimated_minutes=minutes,
        unlock_rule="sequential",
        published=True,
    )
    db.add(lesson)
    db.flush()
    return lesson


def objectives(db, lesson: Lesson, step: LessonStep, items: list[str]) -> None:
    for i, t in enumerate(items):
        add_item(db, lesson_id=lesson.id, step_id=step.id, sort_order=i, item_type="objective", meaning_vi=t)


def tips(db, lesson: Lesson, step: LessonStep, items: list[tuple[str, str]]) -> None:
    for i, (title, body) in enumerate(items):
        add_item(
            db,
            lesson_id=lesson.id,
            step_id=step.id,
            sort_order=i,
            item_type="grammar_tip",
            speaker=title,
            meaning_vi=body,
        )


def cards(db, lesson: Lesson, step: LessonStep, item_type: str, speaker: str | None, items: list[tuple], fmt) -> None:
    for i, row in enumerate(items):
        hz, py, mv = fmt(row)
        add_item(
            db,
            lesson_id=lesson.id,
            step_id=step.id,
            sort_order=i,
            item_type=item_type,
            hanzi=hz,
            pinyin=py,
            meaning_vi=mv,
            audio_text=hz,
            speaker=speaker,
        )


def quizzes(db, lesson: Lesson, step: LessonStep, items: list[dict]) -> None:
    for i, q in enumerate(items):
        add_item(
            db,
            lesson_id=lesson.id,
            step_id=step.id,
            sort_order=i,
            item_type="quiz_prompt",
            hanzi=q["hanzi"],
            pinyin=q["pinyin"],
            meaning_vi=q["prompt"],
            audio_text=q["hanzi"],
            meta={"options": q["options"], "answer": q["answer"], "quiz_kind": "phonics"},
        )


def reviews(db, lesson: Lesson, step: LessonStep, items: list[str]) -> None:
    for i, t in enumerate(items):
        add_item(db, lesson_id=lesson.id, step_id=step.id, sort_order=i, item_type="grammar_tip", meaning_vi=t)


def complete(db, lesson: Lesson, step: LessonStep, text: str) -> None:
    add_item(
        db,
        lesson_id=lesson.id,
        step_id=step.id,
        sort_order=0,
        item_type="media",
        hanzi="完成",
        pinyin="wánchéng",
        meaning_vi=text,
        audio_text="完成",
    )


# ---------------------------------------------------------------------------
# Lesson 1 — Nhập môn & Mẹo phát âm
# ---------------------------------------------------------------------------
def build_lesson_1(db, course: Course) -> None:
    lesson = make_lesson(db, course, 1, "拼音入门", "Nhập môn & Mẹo phát âm", 12)
    steps = build_steps(
        db,
        lesson,
        {
            "objectives": "Mục tiêu",
            "phonics": "Mẹo lưỡi · Miệng · Hơi",
            "vocab": "6 nguyên âm cơ bản",
            "sentences": "Ví dụ ghép âm",
            "practice": "Luyện tập nhanh",
            "review": "Ôn nhanh",
            "complete": "Hoàn thành",
        },
    )
    objectives(
        db,
        lesson,
        steps["objectives"],
        [
            "Hiểu cấu trúc âm tiết tiếng Trung: (thanh mẫu) + vận mẫu + thanh điệu.",
            "Biết dùng gương và tờ giấy để tự kiểm tra khuôn miệng và luồng hơi.",
            "Nhận biết 6 nguyên âm cơ bản: a o e i u ü.",
        ],
    )
    tips(
        db,
        lesson,
        steps["phonics"],
        [
            (
                "Cấu trúc âm tiết",
                "Mỗi chữ Hán ≈ 1 âm tiết = (thanh mẫu) + vận mẫu + thanh điệu. Có thể không có thanh mẫu (a, o, e…) nhưng luôn có vận mẫu + thanh.",
            ),
            (
                "Mẹo gương",
                "Tập trước gương: nhìn rõ môi tròn/dẹt, răng có khép không. a — há miệng to; o/u — môi tròn; i — miệng dẹt cười; ü — môi tròn như u nhưng lưỡi như i.",
            ),
            (
                "Mẹo giấy bật hơi",
                "Để tờ giấy mỏng trước miệng: p / t / k / c / ch / q làm giấy bay; b / d / g / z / zh / j giấy gần như đứng yên. Người Việt hay quên đối lập này — sẽ luyện kỹ ở bài 2 và 3.",
            ),
        ],
    )
    cards(
        db,
        lesson,
        steps["vocab"],
        "vocab_card",
        "6 nguyên âm cơ bản",
        [
            ("a", "ā", "啊", "Há miệng to, lưỡi thấp — như bác sĩ bảo “aaa”"),
            ("o", "ō", "喔", "Môi tròn, lưỡi hơi lùi"),
            ("e", "ē", "鹅", "Miệng nửa mở, không tròn — gần “ơ” kéo dài"),
            ("i", "yī", "一", "Miệng dẹt cười, lưỡi nâng cao phía trước"),
            ("u", "wū", "乌", "Môi tròn nhỏ, lưỡi lùi"),
            ("ü", "yū", "迂", "Lưỡi như i + môi như u (mép tròn)"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    cards(
        db,
        lesson,
        steps["sentences"],
        "sentence_card",
        "Ví dụ ghép âm",
        [
            ("ma", "mā", "妈", "Ghép m + a · thanh 1 — ví dụ đầu tiên của âm tiết hoàn chỉnh"),
            ("ba", "bà", "爸", "Ghép b + a · thanh 4"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    quizzes(
        db,
        lesson,
        steps["practice"],
        [
            {
                "hanzi": "妈",
                "pinyin": "mā",
                "prompt": "妈 (mā) gồm những phần nào?",
                "options": [
                    "Thanh mẫu m + vận mẫu a + thanh 1",
                    "Chỉ có vận mẫu a",
                    "Thanh mẫu m + thanh 4",
                    "Không có cấu trúc cố định",
                ],
                "answer": "Thanh mẫu m + vận mẫu a + thanh 1",
            },
            {
                "hanzi": "乌",
                "pinyin": "wū",
                "prompt": "乌 (wū) — môi ở trạng thái nào?",
                "options": ["Môi tròn nhỏ", "Miệng dẹt cười", "Há miệng to", "Môi mím chặt"],
                "answer": "Môi tròn nhỏ",
            },
        ],
    )
    reviews(
        db,
        lesson,
        steps["review"],
        [
            "Âm tiết = (thanh mẫu) + vận mẫu + thanh điệu — luôn có vận mẫu và thanh.",
            "Dùng gương kiểm tra môi tròn/dẹt; dùng giấy kiểm tra luồng hơi.",
            "6 nguyên âm cơ bản: a o e i u ü — học kỹ trước khi ghép âm.",
        ],
    )
    complete(db, lesson, steps["complete"], "Xong bài 1! Qua bài 2 để học nhóm thanh mẫu dễ: b p m f · d t n l · g k h.")


# ---------------------------------------------------------------------------
# Lesson 2 — Thanh mẫu dễ: Môi · Đầu lưỡi · Gốc lưỡi
# ---------------------------------------------------------------------------
def build_lesson_2(db, course: Course) -> None:
    lesson = make_lesson(db, course, 2, "声母（一）", "Thanh mẫu dễ: Môi · Đầu lưỡi · Gốc lưỡi", 15)
    steps = build_steps(
        db,
        lesson,
        {
            "objectives": "Mục tiêu",
            "phonics": "Mẹo bật hơi",
            "vocab": "Thanh mẫu: b p m f · d t n l · g k h",
            "sentences": "Ghép âm luyện tập",
            "practice": "Luyện tập bật hơi",
            "review": "Ôn nhanh",
            "complete": "Hoàn thành",
        },
    )
    objectives(
        db,
        lesson,
        steps["objectives"],
        [
            "Phát âm đúng 11 thanh mẫu dễ: b p m f (môi), d t n l (đầu lưỡi), g k h (gốc lưỡi).",
            "Phân biệt bật hơi vs không bật hơi: b/p, d/t, g/k.",
            "Ghép được các thanh mẫu này với vận mẫu cơ bản.",
        ],
    )
    tips(
        db,
        lesson,
        steps["phonics"],
        [
            (
                "Nhóm Môi (b p m f)",
                "b, p, m: hai môi chạm nhau rồi mở. f: môi dưới chạm răng trên (như f tiếng Việt). b không bật hơi, p bật hơi mạnh, m có mũi ngân.",
            ),
            (
                "Nhóm Đầu lưỡi (d t n l)",
                "Đầu lưỡi chạm răng cửa trên/lợi trên. d không bật hơi, t bật hơi. n có mũi ngân (chạm sống mũi). l: hơi thoát hai bên lưỡi.",
            ),
            (
                "Nhóm Gốc lưỡi (g k h)",
                "Gốc lưỡi nâng lên chạm vòm mềm phía sau. g không bật hơi, k bật hơi mạnh. h xát nhẹ, nhẹ hơn h tiếng Việt.",
            ),
            (
                "Mẹo giấy bật hơi (nhắc lại)",
                "Cầm tờ giấy mỏng trước miệng: p, t, k làm giấy bay mạnh; b, d, g giấy gần như đứng yên. Luyện từng cặp: bō–pō, dé–tè, gē–kē.",
            ),
        ],
    )
    cards(
        db,
        lesson,
        steps["vocab"],
        "vocab_card",
        None,
        [
            ("b", "bō", "玻", "Môi bpmf · không bật hơi (đối với p)"),
            ("p", "pō", "坡", "Môi bpmf · bật hơi mạnh — giấy phải bay"),
            ("m", "mō", "摸", "Môi bpmf · mũi ngân (cảm mũi)"),
            ("f", "fō", "佛", "Môi bpmf · môi dưới + răng trên"),
            ("d", "dé", "得", "Đầu lưỡi dtnl · không bật hơi"),
            ("t", "tè", "特", "Đầu lưỡi dtnl · bật hơi"),
            ("n", "ne", "呢", "Đầu lưỡi dtnl · mũi ngân (chạm sống mũi)"),
            ("l", "le", "了", "Đầu lưỡi dtnl · hơi thoát hai bên lưỡi (không mũi)"),
            ("g", "gē", "哥", "Gốc lưỡi gkh · không bật hơi"),
            ("k", "kē", "科", "Gốc lưỡi gkh · bật hơi"),
            ("h", "hē", "喝", "Gốc lưỡi gkh · xát nhẹ (không phải h Việt nặng)"),
        ],
        lambda r: (r[2], r[1], f"Thanh mẫu {r[0]} · {r[3]}"),
    )
    cards(
        db,
        lesson,
        steps["sentences"],
        "sentence_card",
        "Ghép âm luyện tập",
        [
            ("ba", "bà", "爸", "Ghép b + a · thanh 4"),
            ("pa", "pá", "爬", "Ghép p + a · thanh 2 (bật hơi)"),
            ("mǎi", "mǎi", "买", "Ghép m + ai · thanh 3"),
            ("nǐ", "nǐ", "你", "Ghép n + i · thanh 3"),
            ("lái", "lái", "来", "Ghép l + ai · thanh 2"),
            ("gē", "gē", "哥", "Ghép g + e · thanh 1"),
            ("hē", "hē", "喝", "Ghép h + e · thanh 1"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    quizzes(
        db,
        lesson,
        steps["practice"],
        [
            {
                "hanzi": "坡",
                "pinyin": "pō",
                "prompt": "So với bō, pō khác ở điểm nào?",
                "options": ["Thanh điệu", "Bật hơi mạnh hơn", "Mũi ngân", "Lưỡi cong"],
                "answer": "Bật hơi mạnh hơn",
            },
            {
                "hanzi": "特",
                "pinyin": "tè",
                "prompt": "特 (tè) là thanh mẫu nào, bật hơi hay không?",
                "options": ["t — bật hơi", "d — không bật hơi", "t — không bật hơi", "n — mũi ngân"],
                "answer": "t — bật hơi",
            },
            {
                "hanzi": "科",
                "pinyin": "kē",
                "prompt": "科 (kē) thuộc nhóm nào?",
                "options": ["Môi bpmf", "Đầu lưỡi dtnl", "Gốc lưỡi gkh", "Mặt lưỡi jqx"],
                "answer": "Gốc lưỡi gkh",
            },
        ],
    )
    reviews(
        db,
        lesson,
        steps["review"],
        [
            "Checklist hơi: p/t/k giấy bay; b/d/g giấy gần đứng yên.",
            "m và n có mũi ngân; l thoát hơi hai bên lưỡi.",
            "h nhẹ hơn h tiếng Việt — chỉ xát nhẹ ở gốc lưỡi.",
        ],
    )
    complete(db, lesson, steps["complete"], "Xong bài 2! Qua bài 3 để học 3 nhóm thanh mẫu khó nhất: j q x · zh ch sh r · z c s.")


# ---------------------------------------------------------------------------
# Lesson 3 — Thanh mẫu khó: Mặt lưỡi · Cong lưỡi · Phẳng lưỡi
# ---------------------------------------------------------------------------
def build_lesson_3(db, course: Course) -> None:
    lesson = make_lesson(db, course, 3, "声母（二）", "Thanh mẫu khó: 3 nhóm lưỡi dễ nhầm", 15)
    steps = build_steps(
        db,
        lesson,
        {
            "objectives": "Mục tiêu",
            "phonics": "Mẹo 3 nhóm lưỡi",
            "vocab": "Thanh mẫu: j q x · zh ch sh r · z c s",
            "sentences": "Ghép âm zi/zhi/ji…",
            "practice": "Luyện phân biệt 3 nhóm",
            "review": "Ôn nhanh",
            "complete": "Hoàn thành",
        },
    )
    objectives(
        db,
        lesson,
        steps["objectives"],
        [
            "Phân biệt 3 nhóm lưỡi dễ nhầm: mặt lưỡi (j q x), cong lưỡi (zh ch sh r), phẳng lưỡi (z c s).",
            "Hiểu vì sao chữ i sau zh/ch/sh/r/z/c/s không đọc như i thường.",
            "Ghép được zi, ci, si, zhi, chi, shi, ri, ji, qi, xi.",
        ],
    )
    tips(
        db,
        lesson,
        steps["phonics"],
        [
            (
                "Ba nhóm lưỡi hay nhầm",
                "Phẳng z/c/s: đầu lưỡi sát răng cửa dưới, hơi xát ra qua khe hẹp. Cong zh/ch/sh/r: đầu lưỡi cuộn về phía vòm cứng. Mặt lưỡi j/q/x: lưỡi phẳng, phần giữa lưỡi nâng lên gần vòm cứng, đầu lưỡi hạ thấp.",
            ),
            (
                "i sau z/c/s/zh/ch/sh/r",
                "Trong zi/ci/si/zhi/chi/shi/ri, chữ i không đọc như “i” tiếng Việt — chỉ là chỗ gắn thanh điệu, âm thực chất là tiếng “rung/buzz” kéo dài ra từ chính phụ âm đầu.",
            ),
            (
                "Mẹo giấy bật hơi (áp dụng nhóm này)",
                "c, ch, q bật hơi mạnh — giấy bay; z, zh, j không bật hơi — giấy gần như đứng yên. x, sh, s đều là âm xát nhẹ, không có phân biệt bật hơi.",
            ),
        ],
    )
    cards(
        db,
        lesson,
        steps["vocab"],
        "vocab_card",
        None,
        [
            ("j", "jī", "机", "Mặt lưỡi jqx · không bật hơi · chỉ ghép i/ü"),
            ("q", "qī", "七", "Mặt lưỡi jqx · bật hơi · gần “ch” nhưng lưỡi phẳng hơn"),
            ("x", "xī", "西", "Mặt lưỡi jqx · xát · cười nhẹ, lưỡi phẳng"),
            ("zh", "zhī", "知", "Cong lưỡi zh ch sh r · không bật hơi"),
            ("ch", "chī", "吃", "Cong lưỡi zh ch sh r · bật hơi"),
            ("sh", "shī", "诗", "Cong lưỡi zh ch sh r · xát"),
            ("r", "rí", "日", "Cong lưỡi zh ch sh r · rung nhẹ, không như r Việt"),
            ("z", "zī", "字", "Phẳng lưỡi z c s · không bật hơi"),
            ("c", "cī", "次", "Phẳng lưỡi z c s · bật hơi (gần ts)"),
            ("s", "sī", "丝", "Phẳng lưỡi z c s · xát"),
        ],
        lambda r: (r[2], r[1], f"Thanh mẫu {r[0]} · {r[3]}"),
    )
    cards(
        db,
        lesson,
        steps["sentences"],
        "sentence_card",
        "Ghép âm zi/zhi/ji…",
        [
            ("zhi", "zhī", "知", "Cong lưỡi + i “buzz”"),
            ("zi", "zì", "字", "Phẳng lưỡi + i “buzz”"),
            ("ji", "jī", "机", "Mặt lưỡi + i thật (đọc như i tiếng Việt)"),
            ("qi", "qì", "气", "Mặt lưỡi bật hơi + i"),
            ("xi", "xǐ", "洗", "Mặt lưỡi xát + i"),
            ("chī", "chī", "吃", "Cong lưỡi bật hơi + i “buzz”"),
            ("shí", "shí", "十", "Cong lưỡi xát + i “buzz” · thanh 2"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    quizzes(
        db,
        lesson,
        steps["practice"],
        [
            {
                "hanzi": "吃",
                "pinyin": "chī",
                "prompt": "吃 (chī) thuộc nhóm lưỡi nào?",
                "options": ["Phẳng z/c/s", "Cong zh/ch/sh/r", "Mặt lưỡi j/q/x", "Môi b/p/m/f"],
                "answer": "Cong zh/ch/sh/r",
            },
            {
                "hanzi": "西",
                "pinyin": "xī",
                "prompt": "西 (xī) thuộc nhóm nào?",
                "options": ["Cong zh/ch/sh", "Phẳng s", "Mặt lưỡi j/q/x", "Gốc lưỡi g/k/h"],
                "answer": "Mặt lưỡi j/q/x",
            },
            {
                "hanzi": "字",
                "pinyin": "zì",
                "prompt": "Trong 字 (zì), chữ i đọc như thế nào?",
                "options": [
                    "Như “i” tiếng Việt bình thường",
                    "Là âm “buzz” kéo dài từ z, không phải nguyên âm i thật",
                    "Không đọc, chỉ để viết",
                    "Đọc như “ư”",
                ],
                "answer": "Là âm “buzz” kéo dài từ z, không phải nguyên âm i thật",
            },
        ],
    )
    reviews(
        db,
        lesson,
        steps["review"],
        [
            "Phẳng z/c/s: đầu lưỡi sát răng dưới. Cong zh/ch/sh/r: lưỡi cuộn lên vòm. Mặt lưỡi j/q/x: lưỡi phẳng, giữa lưỡi nâng.",
            "i sau z/c/s/zh/ch/sh/r chỉ là chỗ gắn thanh, không phải nguyên âm i thật.",
            "j/q/x chỉ ghép với i hoặc ü, không ghép với u thường.",
        ],
    )
    complete(db, lesson, steps["complete"], "Xong bài 3! Qua bài 4 để học vận mẫu (nguyên âm) và cách ghép âm đầy đủ.")


# ---------------------------------------------------------------------------
# Lesson 4 — Vận mẫu & Ghép âm
# ---------------------------------------------------------------------------
def build_lesson_4(db, course: Course) -> None:
    lesson = make_lesson(db, course, 4, "韵母与拼读", "Vận mẫu & Ghép âm", 15)
    steps = build_steps(
        db,
        lesson,
        {
            "objectives": "Mục tiêu",
            "phonics": "Mẹo ü & vận mẫu mũi",
            "vocab": "Vận mẫu đơn, phức, mũi",
            "sentences": "Ghép âm nü/lü/ju…",
            "practice": "Luyện tập vận mẫu",
            "review": "Ôn nhanh",
            "complete": "Hoàn thành",
        },
    )
    objectives(
        db,
        lesson,
        steps["objectives"],
        [
            "Phát âm đúng vận mẫu đơn (a o e i u ü), vận mẫu phức (ai ei ao ou) và vận mẫu mũi (an ang en eng).",
            "Nắm mẹo đọc ü và quy tắc chính tả j/q/x/y + u = ü.",
            "Ghép được các thanh mẫu đã học với vận mẫu để tạo âm tiết hoàn chỉnh.",
        ],
    )
    tips(
        db,
        lesson,
        steps["phonics"],
        [
            (
                "Mẹo ü",
                "Đọc i (miệng cười, răng gần khép) rồi giữ nguyên vị trí lưỡi, chỉ từ từ tròn môi lại → ra ü. Sau j/q/x/y, chữ viết u thực chất là ü (ju = jü, qu = qü, xu = xü, yu = yü).",
            ),
            (
                "Vận mẫu phức (nguyên âm đôi)",
                "ai, ei, ao, ou là 2 nguyên âm trượt liền nhau trong 1 âm tiết — đọc lướt nhanh, không tách rời. Âm đầu rõ hơn, âm sau nhẹ và ngắn.",
            ),
            (
                "Vận mẫu mũi: -n vs -ng",
                "-n (an, en): đầu lưỡi chạm lợi trên, hơi thoát qua mũi — giống n tiếng Việt. -ng (ang, eng): gốc lưỡi nâng lên, không chạm — giống ng cuối trong tiếng Việt (như “ăng”).",
            ),
        ],
    )
    cards(
        db,
        lesson,
        steps["vocab"],
        "vocab_card",
        "Vận mẫu",
        [
            ("ai", "ài", "爱", "Vận mẫu phức · trượt a → i"),
            ("ei", "bēi", "杯", "Vận mẫu phức · trượt e → i"),
            ("ao", "hǎo", "好", "Vận mẫu phức · trượt a → o"),
            ("ou", "ǒu", "偶", "Vận mẫu phức · trượt o → u"),
            ("an", "ān", "安", "Vận mẫu mũi -n · a + đầu lưỡi chạm lợi"),
            ("ang", "āng", "昂", "Vận mẫu mũi -ng · a + gốc lưỡi (không chạm)"),
            ("en", "ēn", "恩", "Vận mẫu mũi -n · e + đầu lưỡi"),
            ("eng", "ēng", "鞥", "Vận mẫu mũi -ng · e + gốc lưỡi"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    cards(
        db,
        lesson,
        steps["sentences"],
        "sentence_card",
        "Ghép âm nü/lü/ju…",
        [
            ("nü", "nǚ", "女", "n + ü (quan trọng với người Việt vì dễ đọc thành u)"),
            ("lü", "lǜ", "绿", "l + ü"),
            ("ju", "jū", "居", "Viết ju = jü · không đọc “u” thuần"),
            ("qu", "qù", "去", "Viết qu = qü · không đọc “u” thuần"),
            ("xu", "xué", "学", "Viết xu = xü + e (xué) · không đọc “u” thuần"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    quizzes(
        db,
        lesson,
        steps["practice"],
        [
            {
                "hanzi": "女",
                "pinyin": "nǚ",
                "prompt": "女 (nǚ) — nguyên âm nào?",
                "options": ["u như “u” Việt", "ü (i + môi tròn)", "i thuần", "o"],
                "answer": "ü (i + môi tròn)",
            },
            {
                "hanzi": "居",
                "pinyin": "jū",
                "prompt": "Pinyin viết ju — đọc thế nào?",
                "options": ["j + u thuần", "j + ü", "zh + u", "z + u"],
                "answer": "j + ü",
            },
            {
                "hanzi": "昂",
                "pinyin": "āng",
                "prompt": "Vận mẫu -ng trong 昂 (āng) phát âm khác -n ở điểm nào?",
                "options": [
                    "Gốc lưỡi nâng lên, không chạm vòm miệng",
                    "Đầu lưỡi chạm lợi trên",
                    "Môi tròn lại",
                    "Không có gì khác biệt",
                ],
                "answer": "Gốc lưỡi nâng lên, không chạm vòm miệng",
            },
        ],
    )
    reviews(
        db,
        lesson,
        steps["review"],
        [
            "ü = lưỡi như i + môi tròn như u; sau j/q/x/y viết u nhưng đọc ü.",
            "Vận mẫu phức (ai/ei/ao/ou) đọc lướt liền, không tách 2 âm.",
            "-n chạm đầu lưỡi vào lợi; -ng gốc lưỡi nâng, không chạm — 2 âm mũi khác hẳn nhau.",
        ],
    )
    complete(db, lesson, steps["complete"], "Xong bài 4! Qua bài 5 — bài cuối: thanh điệu, biến thanh, và ôn tập tổng hợp.")


# ---------------------------------------------------------------------------
# Lesson 5 — Thanh điệu & Ôn tập tổng hợp
# ---------------------------------------------------------------------------
def build_lesson_5(db, course: Course) -> None:
    lesson = make_lesson(db, course, 5, "声调与总复习", "Thanh điệu & Ôn tập tổng hợp", 18)
    steps = build_steps(
        db,
        lesson,
        {
            "objectives": "Mục tiêu",
            "phonics": "Mẹo 4 thanh & biến thanh",
            "vocab": "4 thanh cùng 1 âm: mā má mǎ mà",
            "sentences": "Biến thanh (sandhi)",
            "practice": "Ôn tập tổng hợp",
            "review": "Checklist toàn bài",
            "complete": "Hoàn thành khóa Phát âm nền",
        },
    )
    objectives(
        db,
        lesson,
        steps["objectives"],
        [
            "Đọc chuẩn 4 thanh điệu + thanh nhẹ qua ví dụ mā má mǎ mà ma.",
            "Hiểu quy tắc biến thanh cơ bản khi 2 thanh 3 đứng liền nhau.",
            "Ôn tập tổng hợp toàn bộ thanh mẫu, vận mẫu đã học ở bài 1-4.",
        ],
    )
    tips(
        db,
        lesson,
        steps["phonics"],
        [
            (
                "Thanh điệu = một phần của từ",
                "Cùng âm mā/má/mǎ/mà nhưng nghĩa hoàn toàn khác nhau (mẹ / gai / ngựa / mắng). Tập bằng tay: thanh 1 đưa ngang tay cao; thanh 2 tay đi lên; thanh 3 tay xuống rồi lên; thanh 4 tay chém xuống mạnh; thanh nhẹ ngắn gọn, không nhấn.",
            ),
            (
                "Biến thanh (sandhi) cơ bản",
                "Hai thanh 3 đứng liền nhau: thanh trước đọc gần như thanh 2. Ví dụ 你好 nǐ hǎo → khi nói nhanh gần như ní hǎo. Đây là quy tắc bắt buộc, không phải tùy chọn.",
            ),
            (
                "Luyện tập hàng ngày",
                "Mỗi ngày 3 phút: đọc lại bảng thanh mẫu (bài 2–3) + vận mẫu (bài 4) + 4 thanh (mā má mǎ mà) trước khi học bài HSK 1 tiếp theo — phát âm chuẩn từ đầu sẽ dễ hơn sửa sau.",
            ),
        ],
    )
    cards(
        db,
        lesson,
        steps["vocab"],
        "vocab_card",
        "4 thanh cùng âm ma",
        [
            ("mā", "mā", "妈", "Thanh 1 (phẳng, cao) — mẹ"),
            ("má", "má", "麻", "Thanh 2 (đi lên) — cây gai/vừng"),
            ("mǎ", "mǎ", "马", "Thanh 3 (xuống rồi lên) — con ngựa"),
            ("mà", "mà", "骂", "Thanh 4 (xuống mạnh) — mắng, chửi"),
        ],
        lambda r: (r[2], r[1], r[3]),
    )
    cards(
        db,
        lesson,
        steps["sentences"],
        "sentence_card",
        "Biến thanh (sandhi)",
        [
            ("nǐ hǎo", "nǐ hǎo", "你好", "Hai thanh 3 liền nhau → thanh trước đọc gần như thanh 2 (ní hǎo)"),
            ("hěn hǎo", "hěn hǎo", "很好", "Thanh 3 + thanh 3 → biến thanh tương tự (hén hǎo)"),
        ],
        lambda r: (r[2], r[1], f"{r[0]} · {r[3]}"),
    )
    quizzes(
        db,
        lesson,
        steps["practice"],
        [
            {
                "hanzi": "妈",
                "pinyin": "mā",
                "prompt": "妈 — thanh điệu nào?",
                "options": ["Thanh 1 (phẳng cao)", "Thanh 2 (lên)", "Thanh 3 (xuống-lên)", "Thanh 4 (xuống)"],
                "answer": "Thanh 1 (phẳng cao)",
            },
            {
                "hanzi": "马",
                "pinyin": "mǎ",
                "prompt": "马 — thanh điệu nào?",
                "options": ["Thanh 1 (phẳng cao)", "Thanh 2 (lên)", "Thanh 3 (xuống-lên)", "Thanh 4 (xuống)"],
                "answer": "Thanh 3 (xuống-lên)",
            },
            {
                "hanzi": "你好",
                "pinyin": "nǐ hǎo",
                "prompt": "Khi nói nhanh, 你好 thường biến thanh thế nào?",
                "options": [
                    "Hai thanh 3 giữ nguyên",
                    "Thanh trước gần như thanh 2",
                    "Cả hai thành thanh 1",
                    "Bỏ thanh",
                ],
                "answer": "Thanh trước gần như thanh 2",
            },
            {
                "hanzi": "坡",
                "pinyin": "pō",
                "prompt": "(Ôn bài 2) So với bō, pō khác ở điểm nào?",
                "options": ["Thanh điệu", "Bật hơi mạnh hơn", "Mũi ngân", "Lưỡi cong"],
                "answer": "Bật hơi mạnh hơn",
            },
            {
                "hanzi": "西",
                "pinyin": "xī",
                "prompt": "(Ôn bài 3) 西 xī thuộc nhóm nào?",
                "options": ["Cong zh/ch/sh", "Phẳng s", "Mặt lưỡi j/q/x", "Gốc lưỡi g/k/h"],
                "answer": "Mặt lưỡi j/q/x",
            },
            {
                "hanzi": "女",
                "pinyin": "nǚ",
                "prompt": "(Ôn bài 4) 女 nǚ — nguyên âm nào?",
                "options": ["u như “u” Việt", "ü (i + môi tròn)", "i thuần", "o"],
                "answer": "ü (i + môi tròn)",
            },
        ],
    )
    reviews(
        db,
        lesson,
        steps["review"],
        [
            "4 thanh + thanh nhẹ: mā (1) má (2) mǎ (3) mà (4) ma (nhẹ) — tập bằng tay mỗi ngày.",
            "2 thanh 3 liền nhau → thanh trước đọc gần như thanh 2 (你好 → ní hǎo).",
            "Checklist lưỡi: z/c/s phẳng · zh/ch/sh/r cong · j/q/x mặt lưỡi phẳng phía trước.",
            "Checklist hơi: p/t/k/c/ch/q giấy bay; b/d/g/z/zh/j giấy gần đứng yên.",
            "Checklist ü: i + môi tròn; j/q/x/y + u trong chữ viết = ü.",
        ],
    )
    complete(
        db,
        lesson,
        steps["complete"],
        "Chúc mừng! Bạn đã hoàn thành khóa Phát âm nền (5 bài). Giờ vào HSK 1 để học chào hỏi — nhớ ôn mā má mǎ mà mỗi ngày.",
    )


def main() -> None:
    db = SessionLocal()
    try:
        pinyin = ensure_pinyin_course(db)
        hsk1 = db.query(Course).filter(Course.slug == HSK1_SLUG).first()
        if hsk1 and hsk1.sort_order < 1:
            hsk1.sort_order = 1

        migrate_legacy_single_lesson(db, pinyin, hsk1)

        build_lesson_1(db, pinyin)
        build_lesson_2(db, pinyin)
        build_lesson_3(db, pinyin)
        build_lesson_4(db, pinyin)
        build_lesson_5(db, pinyin)
        db.commit()

        lessons = (
            db.query(Lesson)
            .filter(Lesson.course_id == pinyin.id)
            .order_by(Lesson.number)
            .all()
        )
        for L in lessons:
            n_items = db.query(LessonItem).filter(LessonItem.lesson_id == L.id).count()
            n_steps = db.query(LessonStep).filter(LessonStep.lesson_id == L.id).count()
            print(f"lesson {L.number}: {L.title_vi} — steps={n_steps} items={n_items}")
        hsk_count = db.query(Lesson).filter(Lesson.course_id == hsk1.id).count() if hsk1 else 0
        print(f"OK course=pinyin lessons={len(lessons)} hsk1_lessons={hsk_count}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
