#!/usr/bin/env python3
"""Rebuild lessons_draft.json from full OCR using TOC title anchors."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HSK1 = ROOT / "data" / "curriculum" / "hsk1"
OCR = HSK1 / "ocr"
TOC = HSK1 / "toc_map.json"
OUT = HSK1 / "lessons_draft.json"

SECTION_HINTS = [
    (r"目标|Objectives", "objectives"),
    (r"热身|Warm[- ]?Up", "warmup"),
    (r"跟读绕口令|Tongue Twister|Shadow the Tongue", "tongue_twister"),
    (r"课文\s*[123]|Text\s*[123]", "text"),
    (r"生词|New Words", "vocab"),
    (r"小语讲堂|Xiaoyu'?s Classroom", "grammar"),
    (r"小语助力|Xiaoyu'?s Tip", "tip"),
    (r"综合练习|Comprehensive Exercises?", "exercise"),
    (r"课堂活动|Classroom Activity", "activity"),
    (r"小语的彩蛋|Bonus Content", "bonus"),
    (r"学习小结|Learning Summary", "summary"),
]


def plain_page(n: int) -> str:
    fp = OCR / f"page_{n:03d}.txt"
    if not fp.exists():
        return ""
    raw = fp.read_text(encoding="utf-8")
    return "\n".join(line.split("|", 1)[-1] if "|" in line else line for line in raw.splitlines())


def detect_type(line: str) -> str | None:
    for pat, kind in SECTION_HINTS:
        if re.search(pat, line, re.I) and len(line) < 100:
            return kind
    return None


def find_start(title_zh: str, search_from: int, search_to: int) -> int | None:
    # prefer pages that look like lesson openers (title near top + 目标/Lesson)
    needle = title_zh.replace("！", "").replace("!", "").strip()
    best = None
    for n in range(search_from, search_to + 1):
        text = plain_page(n)
        head = "\n".join(text.splitlines()[:12])
        if needle[:4] in head or title_zh in head:
            if re.search(r"目标|Objectives|Lesson", head, re.I) or n == search_from:
                return n
            if best is None:
                best = n
    return best


def segment_pages(pages: list[int]) -> list[dict]:
    sections: list[dict] = []
    for page in pages:
        plain = plain_page(page)
        buf_title = f"Trang PDF {page}"
        buf_type = "other"
        buf_lines: list[str] = []
        for line in plain.splitlines():
            kind = detect_type(line)
            if kind:
                if buf_lines and any(x.strip() for x in buf_lines):
                    sections.append(
                        {
                            "type": buf_type,
                            "title": buf_title[:240],
                            "content": "\n".join(buf_lines).strip(),
                            "page": page,
                            "image_url": f"/api/media/curriculum/hsk1/pages/page_{page:03d}.jpg",
                        }
                    )
                buf_type = kind
                buf_title = line.strip()[:240]
                buf_lines = []
            else:
                buf_lines.append(line)
        if buf_lines and any(x.strip() for x in buf_lines):
            sections.append(
                {
                    "type": buf_type,
                    "title": buf_title[:240],
                    "content": "\n".join(buf_lines).strip(),
                    "page": page,
                    "image_url": f"/api/media/curriculum/hsk1/pages/page_{page:03d}.jpg",
                }
            )
    return sections


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    toc = json.loads(TOC.read_text(encoding="utf-8"))
    lessons_meta = toc["lessons"]
    # Exact starts from OCR scan (override approx)
    known_starts = {
        1: 15,
        2: 19,
        3: 24,
        4: 32,
        5: 41,
        6: 49,
        7: 59,
        8: 68,
        9: 75,
        10: 84,
        11: 92,
        12: 100,
        13: 109,
        14: 117,
        15: 126,
    }
    last_content_page = 135  # before vocab index etc.

    lessons = []
    gaps = []
    for i, meta in enumerate(lessons_meta):
        num = int(meta["number"])
        start = known_starts.get(num) or meta.get("pdf_page_approx")
        if not start:
            gaps.append({"type": "no_start_page", "lesson": num})
            continue
        # end = day before next lesson start
        if i + 1 < len(lessons_meta):
            nxt = known_starts.get(int(lessons_meta[i + 1]["number"]))
            end = (nxt - 1) if nxt else last_content_page
        else:
            end = last_content_page
        pages = list(range(int(start), int(end) + 1))
        # verify title presence
        first_text = plain_page(int(start))
        if meta["title_zh"][:4] not in first_text and meta["title_zh"] not in first_text:
            gaps.append(
                {
                    "type": "title_mismatch",
                    "lesson": num,
                    "expected": meta["title_zh"],
                    "page": start,
                    "preview": first_text[:120],
                }
            )
        sections = segment_pages(pages)
        lessons.append(
            {
                "number": num,
                "title_zh": meta["title_zh"],
                "title_en": meta.get("title_en"),
                "grammar_points": meta.get("grammar") or [],
                "page_start": start,
                "page_end": end,
                "pages": pages,
                "sections": sections,
                "cover_image_url": f"/api/media/curriculum/hsk1/pages/page_{int(start):03d}.jpg",
            }
        )
        print(
            f"L{num}: pages {start}-{end} ({len(pages)}p) sections={len(sections)} {meta['title_zh']}",
            flush=True,
        )

    # front matter pages 1-14 as course extras note
    draft = {
        "source_pdf": "document/新HSK教程1.pdf",
        "source_note": "Full OCR of 143 scanned pages. Copyright FLTRP/CTI.",
        "expected_lessons": 15,
        "detected_lessons": len(lessons),
        "pages_ocrd": len(list(OCR.glob("page_*.txt"))),
        "front_matter_pages": list(range(1, 15)),
        "back_matter_pages": list(range(last_content_page + 1, 144)),
        "book_meta": toc.get("book"),
        "lessons": lessons,
        "gaps": gaps,
    }
    OUT.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} lessons={len(lessons)} gaps={len(gaps)}", flush=True)
    # summary sizes
    total_sec = sum(len(L["sections"]) for L in lessons)
    total_chars = sum(len(s["content"]) for L in lessons for s in L["sections"])
    print(f"sections={total_sec} content_chars={total_chars}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
