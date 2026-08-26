#!/usr/bin/env python3
"""Export all pages from 新HSK教程1.pdf, OCR, and draft lesson JSON.

Usage:
  python scripts/extract_hsk1_curriculum.py [--pages-only] [--ocr-only] [--from N] [--to N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "document" / "新HSK教程1.pdf"
OUT = ROOT / "data" / "curriculum" / "hsk1"
PAGES = OUT / "pages"
OCR_DIR = OUT / "ocr"
MANIFEST = OUT / "manifest.json"
DRAFT = OUT / "lessons_draft.json"

# Lesson title patterns seen in OCR (Chinese + Lesson N)
LESSON_RE = re.compile(
    r"(?:第\s*([0-9０-９一二三四五六七八九十]+)\s*课)|(?:Lesson\s*([0-9]{1,2})\b)",
    re.I,
)
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


def export_pages(start: int, end: int | None) -> int:
    import pymupdf

    PAGES.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(PDF))
    total = doc.page_count
    last = min(end or total, total)
    first = max(1, start)
    print(f"Exporting pages {first}-{last} of {total}…", flush=True)
    for i in range(first - 1, last):
        page = doc[i]
        imgs = page.get_images(full=True)
        fp = PAGES / f"page_{i + 1:03d}.jpg"
        if imgs:
            xref = imgs[0][0]
            pix = pymupdf.Pixmap(doc, xref)
            if pix.n > 4:
                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
            pix.save(str(fp))
        else:
            pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
            pix.save(str(fp))
        print(f"  saved {fp.name} ({fp.stat().st_size // 1024} KB)", flush=True)
    return total


def ocr_pages(start: int, end: int | None) -> None:
    from rapidocr_onnxruntime import RapidOCR

    OCR_DIR.mkdir(parents=True, exist_ok=True)
    ocr = RapidOCR()
    files = sorted(PAGES.glob("page_*.jpg"))
    if not files:
        # also accept full_*.jpg from earlier runs
        files = sorted(PAGES.glob("full_*.jpg"))
    selected = []
    for fp in files:
        m = re.search(r"(\d+)", fp.stem)
        if not m:
            continue
        n = int(m.group(1))
        if n < start:
            continue
        if end and n > end:
            continue
        selected.append((n, fp))
    print(f"OCR {len(selected)} pages…", flush=True)
    pages_meta = []
    for n, fp in selected:
        out_txt = OCR_DIR / f"page_{n:03d}.txt"
        out_json = OCR_DIR / f"page_{n:03d}.json"
        print(f"  OCR page {n}…", flush=True)
        result, elapse = ocr(str(fp))
        lines = []
        payloads = []
        if result:
            for box, text, score in result:
                lines.append(f"{score:.2f}|{text}")
                payloads.append({"text": text, "score": float(score), "box": box})
        out_txt.write_text("\n".join(lines), encoding="utf-8")
        out_json.write_text(json.dumps(payloads, ensure_ascii=False), encoding="utf-8")
        plain = "\n".join(p["text"] for p in payloads)
        pages_meta.append(
            {
                "page": n,
                "image": str(fp.relative_to(ROOT)).replace("\\", "/"),
                "ocr_txt": str(out_txt.relative_to(ROOT)).replace("\\", "/"),
                "line_count": len(payloads),
                "preview": plain[:200],
            }
        )
        print(f"    lines={len(payloads)} elapse={elapse}", flush=True)
    MANIFEST.write_text(json.dumps({"pages": pages_meta}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {MANIFEST}", flush=True)


def _detect_section_type(text: str) -> str | None:
    for pat, kind in SECTION_HINTS:
        if re.search(pat, text, re.I):
            return kind
    return None


def build_draft() -> dict:
    """Segment OCR pages into lessons/sections by heuristics."""
    page_texts: dict[int, str] = {}
    for fp in sorted(OCR_DIR.glob("page_*.txt")):
        m = re.search(r"(\d+)", fp.stem)
        if not m:
            continue
        page_texts[int(m.group(1))] = fp.read_text(encoding="utf-8")

    lessons: list[dict] = []
    current: dict | None = None
    for page in sorted(page_texts):
        raw = page_texts[page]
        plain = "\n".join(
            line.split("|", 1)[1] if "|" in line else line for line in raw.splitlines()
        )
        # Lesson start detection
        found_lesson = None
        for line in plain.splitlines()[:25]:
            m = LESSON_RE.search(line)
            if m:
                num = m.group(2) or m.group(1)
                # normalize Chinese numerals lightly
                cmap = {
                    "一": "1",
                    "二": "2",
                    "三": "3",
                    "四": "4",
                    "五": "5",
                    "六": "6",
                    "七": "7",
                    "八": "8",
                    "九": "9",
                    "十": "10",
                    "十一": "11",
                    "十二": "12",
                    "十三": "13",
                    "十四": "14",
                    "十五": "15",
                }
                if num in cmap:
                    num = cmap[num]
                try:
                    found_lesson = int(num)
                except ValueError:
                    found_lesson = None
                if found_lesson:
                    break
        if found_lesson and (current is None or current["number"] != found_lesson):
            if current:
                current["page_end"] = page - 1
                lessons.append(current)
            # title guess: first non-empty line with Chinese
            title_zh = ""
            for line in plain.splitlines():
                if re.search(r"[\u4e00-\u9fff]{2,}", line) and "课" not in line[:2]:
                    title_zh = re.sub(r"^[\d\.\s]+", "", line.strip())[:80]
                    break
            current = {
                "number": found_lesson,
                "title_zh": title_zh or f"第{found_lesson}课",
                "page_start": page,
                "page_end": page,
                "sections": [],
                "raw_pages": [],
            }
        if current is None:
            # front matter
            continue
        current["page_end"] = page
        current["raw_pages"].append(
            {
                "page": page,
                "image": f"data/curriculum/hsk1/pages/page_{page:03d}.jpg",
                "text": plain,
            }
        )
        # split page into crude sections by heading lines
        buf_title = f"Trang {page}"
        buf_type = "other"
        buf_lines: list[str] = []
        for line in plain.splitlines():
            kind = _detect_section_type(line)
            if kind and len(line) < 80:
                if buf_lines:
                    current["sections"].append(
                        {
                            "type": buf_type,
                            "title": buf_title,
                            "content": "\n".join(buf_lines).strip(),
                            "page": page,
                            "image_url": None,
                        }
                    )
                buf_type = kind
                buf_title = line.strip()[:120]
                buf_lines = []
            else:
                buf_lines.append(line)
        if buf_lines:
            current["sections"].append(
                {
                    "type": buf_type,
                    "title": buf_title,
                    "content": "\n".join(buf_lines).strip(),
                    "page": page,
                    "image_url": f"/media/curriculum/hsk1/page_{page:03d}.jpg",
                }
            )

    if current:
        lessons.append(current)

    draft = {
        "source_pdf": "document/新HSK教程1.pdf",
        "source_note": "OCR draft from scanned PDF. Copyright: FLTRP / CTI 《新HSK教程》. Use only if you hold rights.",
        "expected_lessons": 15,
        "detected_lessons": len(lessons),
        "pages_ocrd": len(page_texts),
        "book_meta": {
            "title": "新HSK教程1 / New HSK Course 1",
            "vocab_target": 300,
            "language_points": 40,
            "hours": "30-36",
            "structure": [
                "objectives",
                "tongue_twister (L1-3) / warmup (L4-15)",
                "text x3 + vocab + grammar (小语讲堂)",
                "exercise",
                "activity",
                "bonus (8 total)",
                "summary (every 3 lessons)",
            ],
        },
        "lessons": lessons,
        "gaps": [],
    }
    missing = [n for n in range(1, 16) if not any(L["number"] == n for L in lessons)]
    if missing:
        draft["gaps"].append({"type": "missing_lessons", "numbers": missing})
    if len(page_texts) < 143:
        draft["gaps"].append(
            {"type": "incomplete_ocr", "have": len(page_texts), "need": 143}
        )
    DRAFT.write_text(json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {DRAFT} lessons={len(lessons)} gaps={draft['gaps']}", flush=True)
    return draft


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--pages-only", action="store_true")
    ap.add_argument("--ocr-only", action="store_true")
    ap.add_argument("--draft-only", action="store_true")
    ap.add_argument("--from", dest="start", type=int, default=1)
    ap.add_argument("--to", dest="end", type=int, default=None)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.draft_only:
        build_draft()
        return 0
    if not args.ocr_only:
        export_pages(args.start, args.end)
        if args.pages_only:
            return 0
    ocr_pages(args.start, args.end)
    build_draft()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
