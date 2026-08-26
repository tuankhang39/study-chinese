"""Lesson-type pipelines for the HSK lesson player."""

from __future__ import annotations

from typing import Any

# step_key → default Vietnamese title
STEP_TITLES: dict[str, str] = {
    "objectives": "Mục tiêu",
    "phonics": "Phát âm / Pinyin",
    "tongue_twister": "Đọc theo · Vần điệu",
    "warmup": "Khởi động",
    "vocab": "Từ vựng",
    "sentences": "Câu mẫu · Phát âm",
    "dialogue": "Hội thoại",
    "grammar": "Ngữ pháp",
    "practice": "Luyện tập",
    "review": "Tóm tắt · Ôn",
    "complete": "Hoàn thành",
}

# Ordered pipelines per lesson_type
LESSON_TYPE_PIPELINES: dict[str, list[str]] = {
    "dialogue_core": [
        "objectives",
        "vocab",
        "sentences",
        "dialogue",
        "grammar",
        "practice",
        "complete",
    ],
    "survival_phrases": [
        "objectives",
        "vocab",
        "sentences",
        "dialogue",
        "practice",
        "complete",
    ],
    "phonics_focus": [
        "objectives",
        "phonics",
        "vocab",
        "sentences",
        "complete",
    ],
    "grammar_focus": [
        "objectives",
        "vocab",
        "grammar",
        "sentences",
        "dialogue",
        "practice",
        "complete",
    ],
    "review_summary": [
        "objectives",
        "review",
        "practice",
        "complete",
    ],
    "culture_bonus": [
        "objectives",
        "vocab",
        "grammar",
        "complete",
    ],
    "workplace_scene": [
        "objectives",
        "vocab",
        "sentences",
        "dialogue",
        "grammar",
        "practice",
        "complete",
    ],
}

LESSON_TYPES = set(LESSON_TYPE_PIPELINES.keys())

# HSK1 lesson number → lesson_type
HSK1_LESSON_TYPES: dict[int, str] = {
    1: "survival_phrases",
    2: "dialogue_core",
    3: "grammar_focus",
    4: "grammar_focus",
    5: "dialogue_core",
    6: "workplace_scene",  # phone number
    7: "workplace_scene",  # finish work time
    8: "workplace_scene",  # hospital
    9: "dialogue_core",
    10: "dialogue_core",
    11: "grammar_focus",
    12: "grammar_focus",
    13: "dialogue_core",
    14: "grammar_focus",
    15: "workplace_scene",  # airport
}

# Extra steps inserted for L2–3 (tongue twister after objectives)
HSK1_EXTRA_STEPS: dict[int, list[tuple[int, str]]] = {
    # insert_at_index, step_key
    2: [(1, "tongue_twister")],
    3: [(1, "tongue_twister")],
}


def pipeline_for_type(lesson_type: str, lesson_number: int | None = None) -> list[dict[str, Any]]:
    """Return list of {step_key, title_vi, sort_order, required} for a lesson type."""
    keys = list(LESSON_TYPE_PIPELINES.get(lesson_type) or LESSON_TYPE_PIPELINES["dialogue_core"])
    if lesson_number and lesson_number in HSK1_EXTRA_STEPS:
        for idx, key in HSK1_EXTRA_STEPS[lesson_number]:
            if key not in keys:
                keys.insert(min(idx, len(keys)), key)
    steps = []
    for i, key in enumerate(keys):
        steps.append(
            {
                "step_key": key,
                "title_vi": STEP_TITLES.get(key, key),
                "sort_order": i,
                "required": key != "complete",
            }
        )
    return steps


def lesson_type_for_hsk1(number: int) -> str:
    return HSK1_LESSON_TYPES.get(number, "dialogue_core")
