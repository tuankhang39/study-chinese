"""Parse OCR lesson draft sections into structured lesson items."""

from __future__ import annotations

import re
from typing import Any

# Common Hanzi words that appear as vocab heads
HANZI_LINE = re.compile(r"^[\u4e00-\u9fff]{1,8}$")
PINYIN_LINE = re.compile(
    r"^[A-Za-züÜǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ\s\-']{2,40}$"
)
SPEAKER_NAMES = {
    "王一飞",
    "小语",
    "白家月",
    "安妮",
    "陈天中",
    "李文",
    "王一雪",
    "刘明",
    "学生们",
    "同学们",
    "老师",
    "Wang Yifei",
    "Xiaoyu",
    "Bai Jiayue",
    "Annie",
    "Chen Tianzhong",
    "Li Wen",
}


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in (text or "").splitlines() if ln.strip()]


def parse_objectives(content: str) -> list[dict[str, Any]]:
    items = []
    for i, ln in enumerate(_lines(content)):
        # Prefer lines with Chinese
        if re.search(r"[\u4e00-\u9fff]", ln) and len(ln) > 8:
            zh = re.sub(r"[A-Za-z].*$", "", ln).strip(" .。")
            en = ""
            m = re.search(r"(Be able|Understand|[A-Z][a-z].{10,})", ln)
            if m:
                en = m.group(0).strip()
            items.append(
                {
                    "item_type": "objective",
                    "hanzi": zh or ln[:120],
                    "meaning_en": en or None,
                    "meaning_vi": None,
                    "sort_order": i,
                }
            )
    if not items and content.strip():
        items.append(
            {
                "item_type": "objective",
                "hanzi": content.strip()[:200],
                "sort_order": 0,
            }
        )
    return items[:6]


def parse_vocab(content: str) -> list[dict[str, Any]]:
    """Heuristic: consecutive hanzi / pinyin / english gloss."""
    lines = _lines(content)
    items: list[dict[str, Any]] = []
    i = 0
    seen: set[str] = set()
    while i < len(lines):
        ln = lines[i]
        # skip noise
        if re.search(r"New Words|生词|Proper Noun|专有|Role-play|Work in|分角色|001|002|003", ln, re.I):
            i += 1
            continue
        if ":" in ln and re.search(r"[A-Za-z]", ln) and not HANZI_LINE.match(ln.split(":")[0]):
            # English dialogue translation line
            i += 1
            continue
        # Pattern: 你好 / ni hao / hello  OR 大家dajia
        glued = re.match(r"^([\u4e00-\u9fff]{1,8})([A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔù\s]+)$", ln)
        if glued:
            hanzi, pinyin = glued.group(1), glued.group(2).strip()
            meaning = ""
            if i + 1 < len(lines) and not HANZI_LINE.match(lines[i + 1]) and not re.search(r"[\u4e00-\u9fff]", lines[i + 1]):
                meaning = lines[i + 1]
                i += 1
            if hanzi not in seen:
                seen.add(hanzi)
                items.append(
                    {
                        "item_type": "vocab_card",
                        "hanzi": hanzi,
                        "pinyin": pinyin,
                        "meaning_en": meaning or None,
                        "meaning_vi": None,
                        "audio_text": hanzi,
                        "sort_order": len(items),
                    }
                )
            i += 1
            continue
        if HANZI_LINE.match(ln) and ln not in SPEAKER_NAMES:
            hanzi = ln
            pinyin = ""
            meaning = ""
            if i + 1 < len(lines) and PINYIN_LINE.match(lines[i + 1].replace(".", "")):
                pinyin = lines[i + 1]
                i += 1
            if i + 1 < len(lines):
                nxt = lines[i + 1]
                if not HANZI_LINE.match(nxt) and not re.search(r"[\u4e00-\u9fff]{3,}", nxt):
                    if re.search(r"[a-zA-Z]", nxt) or len(nxt) < 40:
                        meaning = nxt
                        i += 1
            if hanzi not in seen and len(hanzi) <= 6:
                seen.add(hanzi)
                items.append(
                    {
                        "item_type": "vocab_card",
                        "hanzi": hanzi,
                        "pinyin": pinyin or None,
                        "meaning_en": meaning or None,
                        "meaning_vi": None,
                        "audio_text": hanzi,
                        "sort_order": len(items),
                    }
                )
        i += 1
    return items[:40]


def parse_dialogue(content: str) -> list[dict[str, Any]]:
    """Extract dialogue lines: speaker + Chinese utterance."""
    lines = _lines(content)
    items: list[dict[str, Any]] = []
    # Collect lines that are mostly Chinese and look like speech
    for i, ln in enumerate(lines):
        if re.search(r"朗读|Read the|Role-play|Work in|Text \d|课文|On the first|生词|New Words", ln, re.I):
            continue
        # "AI小语，你好!" style
        if re.search(r"[\u4e00-\u9fff]", ln) and len(ln) <= 40:
            # skip pure vocab heads of 1-2 chars without punctuation unless greeting-like
            if HANZI_LINE.match(ln) and ln in SPEAKER_NAMES:
                continue
            if HANZI_LINE.match(ln) and len(ln) <= 2 and ln not in {"你好", "谢谢", "再见"}:
                continue
            speaker = None
            # look back for speaker name
            for j in range(i - 1, max(-1, i - 4), -1):
                prev = lines[j]
                if prev in SPEAKER_NAMES or re.match(r"^[\u4e00-\u9fff]{2,4}$", prev):
                    if prev not in {"你好", "谢谢", "再见", "不客气"}:
                        speaker = prev
                        break
            # skip if looks like vocab gloss block
            if re.match(r"^[\u4e00-\u9fff]+$", ln) and i + 1 < len(lines) and PINYIN_LINE.match(lines[i + 1]):
                continue
            items.append(
                {
                    "item_type": "dialogue_line",
                    "hanzi": ln,
                    "pinyin": None,
                    "speaker": speaker,
                    "audio_text": re.sub(r"[^\u4e00-\u9fff，。！？、]", "", ln) or ln,
                    "sort_order": len(items),
                }
            )
    # also promote short phrases to sentence_card later
    return items[:24]


def parse_sentences_from_dialogue(dialogue_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for d in dialogue_items:
        hanzi = d.get("hanzi") or ""
        if not hanzi:
            continue
        out.append(
            {
                "item_type": "sentence_card",
                "hanzi": hanzi,
                "pinyin": d.get("pinyin"),
                "meaning_en": None,
                "meaning_vi": None,
                "audio_text": d.get("audio_text") or hanzi,
                "speaker": d.get("speaker"),
                "sort_order": len(out),
            }
        )
    return out[:12]


def parse_grammar(content: str, grammar_points: list[Any] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if grammar_points:
        for i, g in enumerate(grammar_points):
            items.append(
                {
                    "item_type": "grammar_tip",
                    "hanzi": str(g)[:200],
                    "meaning_vi": None,
                    "sort_order": i,
                }
            )
    # also take first Chinese-heavy paragraphs
    buf = []
    for ln in _lines(content):
        if re.search(r"[\u4e00-\u9fff]", ln) and len(ln) > 10:
            buf.append(ln)
    for i, ln in enumerate(buf[:4]):
        if any(ln[:20] in (it.get("hanzi") or "") for it in items):
            continue
        items.append(
            {
                "item_type": "grammar_tip",
                "hanzi": ln[:240],
                "sort_order": len(items),
            }
        )
    return items[:8]


def build_quiz_from_vocab(vocab_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Simple match quiz: show hanzi, options from meanings."""
    quizzes = []
    pool = [v for v in vocab_items if v.get("hanzi") and (v.get("meaning_en") or v.get("meaning_vi"))]
    for i, v in enumerate(pool[:8]):
        correct = v.get("meaning_vi") or v.get("meaning_en") or ""
        distractors = []
        for o in pool:
            m = o.get("meaning_vi") or o.get("meaning_en") or ""
            if m and m != correct and m not in distractors:
                distractors.append(m)
            if len(distractors) >= 3:
                break
        while len(distractors) < 3:
            distractors.append(f"(lựa chọn {len(distractors)+1})")
        options = [correct] + distractors[:3]
        # rotate so correct isn't always first
        options = options[1:] + options[:1] if i % 2 else options
        quizzes.append(
            {
                "item_type": "quiz_prompt",
                "hanzi": v["hanzi"],
                "pinyin": v.get("pinyin"),
                "audio_text": v.get("audio_text") or v["hanzi"],
                "meaning_vi": correct,
                "meta": {
                    "quiz_kind": "match_meaning",
                    "options": options,
                    "answer": correct,
                },
                "sort_order": i,
            }
        )
    return quizzes


def items_from_lesson_draft(lesson: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Return items grouped by step_key."""
    sections = lesson.get("sections") or []
    by_step: dict[str, list[dict[str, Any]]] = {
        "objectives": [],
        "vocab": [],
        "sentences": [],
        "dialogue": [],
        "grammar": [],
        "practice": [],
        "phonics": [],
        "tongue_twister": [],
        "warmup": [],
        "review": [],
    }

    all_dialogue: list[dict[str, Any]] = []
    all_vocab: list[dict[str, Any]] = []

    for sec in sections:
        stype = sec.get("type") or "other"
        content = sec.get("content") or ""
        page = sec.get("page")
        if stype == "objectives":
            for it in parse_objectives(content):
                it["source_page"] = page
                by_step["objectives"].append(it)
        elif stype == "vocab":
            for it in parse_vocab(content):
                it["source_page"] = page
                all_vocab.append(it)
                by_step["vocab"].append(it)
        elif stype == "text":
            dial = parse_dialogue(content)
            for it in dial:
                it["source_page"] = page
                all_dialogue.append(it)
                by_step["dialogue"].append(it)
        elif stype == "grammar":
            for it in parse_grammar(content, lesson.get("grammar_points")):
                it["source_page"] = page
                by_step["grammar"].append(it)
        elif stype == "tongue_twister":
            for it in parse_dialogue(content)[:5]:
                it["item_type"] = "sentence_card"
                it["source_page"] = page
                by_step["tongue_twister"].append(it)
        elif stype in ("tip", "bonus"):
            for it in parse_grammar(content)[:3]:
                it["source_page"] = page
                by_step["grammar"].append(it)
        elif stype == "summary":
            for it in parse_objectives(content)[:5]:
                it["source_page"] = page
                by_step["review"].append(it)

    # sentences from dialogue
    for it in parse_sentences_from_dialogue(all_dialogue):
        by_step["sentences"].append(it)

    # grammar from lesson meta if empty
    if not by_step["grammar"] and lesson.get("grammar_points"):
        by_step["grammar"] = parse_grammar("", lesson.get("grammar_points"))

    # practice quizzes
    by_step["practice"] = build_quiz_from_vocab(all_vocab or by_step["vocab"])

    # dedupe vocab by hanzi
    seen = set()
    uniq = []
    for v in by_step["vocab"]:
        h = v.get("hanzi")
        if h and h not in seen:
            seen.add(h)
            uniq.append(v)
    by_step["vocab"] = uniq

    return by_step
