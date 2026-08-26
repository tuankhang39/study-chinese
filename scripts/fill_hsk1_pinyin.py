#!/usr/bin/env python3
"""Fill missing/bad pinyin for all Chinese lesson_items (+ vocabulary)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, "/app")

from app.core.database import SessionLocal  # noqa: E402
from app.models import LessonItem, Vocabulary  # noqa: E402
from app.services.pinyin_util import ensure_pinyin, has_hanzi, is_good_pinyin  # noqa: E402


def main() -> None:
    db = SessionLocal()
    updated_items = 0
    updated_vocab = 0
    try:
        for it in db.query(LessonItem).all():
            if not has_hanzi(it.hanzi):
                continue
            new_py = ensure_pinyin(it.hanzi, it.pinyin)
            if new_py and new_py != (it.pinyin or "").strip():
                it.pinyin = new_py
                updated_items += 1
            elif not is_good_pinyin(it.pinyin) and new_py:
                it.pinyin = new_py
                updated_items += 1

        for v in db.query(Vocabulary).all():
            if not has_hanzi(v.hanzi):
                continue
            new_py = ensure_pinyin(v.hanzi, v.pinyin)
            if new_py and new_py != (v.pinyin or "").strip():
                v.pinyin = new_py
                updated_vocab += 1

        db.commit()
        print(f"updated_items={updated_items} updated_vocab={updated_vocab}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
