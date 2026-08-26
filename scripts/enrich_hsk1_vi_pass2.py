#!/usr/bin/env python3
"""Second-pass: better VI translations + remove exercise OCR fragments."""

from __future__ import annotations

import json
import re
import sys

sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models import LessonItem, Vocabulary

# English meaning_vi that leaked from bank → proper VI
EN_LEAK = {
    "everyone": "mọi người",
    "you (courteous, as opposed to informal 你)": "ngài / bạn (kính ngữ)",
    "you": "bạn",
    "hello": "xin chào",
    "goodbye": "tạm biệt",
    "thank you": "cảm ơn",
    "teacher": "giáo viên",
    "student": "học sinh / sinh viên",
    "good": "tốt",
    "fine": "tốt",
}

SENTENCE_VI = {
    "AI小语，你好!": "Xin chào AI Tiểu Ngữ!",
    "AI小语，你好！": "Xin chào AI Tiểu Ngữ!",
    "王老师，你好!": "Xin chào cô/thầy Vương!",
    "王老师，你好！": "Xin chào cô/thầy Vương!",
    "你好，安妮！": "Xin chào Annie!",
    "你好，陈天中！我不": "Xin chào Trần Thiên Trung! Tôi không…",
    "是安妮，我是白家月": "Không phải Annie, tôi là Bạch Gia Nguyệt",
    "对不起！": "Xin lỗi!",
    "我是中国人。": "Tôi là người Trung Quốc.",
    "我是法国人。我": "Tôi là người Pháp. Tôi…",
    "的中文老师也是": "…giáo viên tiếng Trung cũng là…",
    "中国人。": "người Trung Quốc.",
    "飞忙吗？": "(Vương Nhất) Phi bận không?",
    "她很忙。": "Cô ấy rất bận.",
    "她有多少个学生？": "Cô ấy có bao nhiêu học sinh?",
    "大家好！": "Xin chào mọi người!",
    "老师，您好！": "Thưa thầy/cô, xin chào!",
    "你们好！": "Xin chào các bạn!",
    "你好，小语!": "Xin chào Tiểu Ngữ!",
    "你好，小语！": "Xin chào Tiểu Ngữ!",
    "谢谢!": "Cảm ơn!",
    "谢谢！": "Cảm ơn!",
    "不客气！": "Không có gì!",
    "同学们，再见!": "Các bạn, tạm biệt!",
    "同学们，再见！": "Các bạn, tạm biệt!",
    "老师，再见!": "Thưa thầy/cô, tạm biệt!",
    "老师，再见！": "Thầy/cô, tạm biệt!",
    "我叫李文。": "Tôi tên Lý Văn.",
    "你好！我叫李文。": "Xin chào! Tôi tên Lý Văn.",
    "中国人的姓名：姓+名": "Tên người Trung Quốc: họ + tên",
    "“谁”也可以读成“shu”": "“谁” cũng có thể đọc là “shuí”",
    "七加一，再减一，加完减完等于几？加完减完还是七。": "Bảy cộng một, rồi trừ một… kết quả vẫn là bảy. (vần điệu số)",
    "十四是十四，四十是四十。": "Mười bốn là mười bốn, bốn mươi là bốn mươi. (vần điệu)",
    "B很冷": "Rất lạnh",
    "C有点儿冷": "Hơi lạnh",
    "A上班": "Đi làm",
    "没事": "Không sao / không có việc gì",
}

GRAMMAR_VI = {
    "表示人或事物等同什么或类属什么，否定形式是“不是”。": "Dùng để nói A là B (đồng nhất / thuộc loại). Phủ định: “不是”.",
    "“吗”是语气助词，通常在句子末尾，表示疑问。基本结构：···吗？": "“吗” là trợ từ ngữ khí cuối câu, tạo câu hỏi đúng/sai. Cấu trúc: …吗？",
    "The basic word order in Chinese is: Subject+Predic": "Trật tự cơ bản tiếng Trung: Chủ ngữ + Vị ngữ (+ Tân ngữ).",
    "The “是” sentence is used to indicate what somebody": "Câu “是” dùng để nói ai/cái gì là gì.",
    "negative form is “不是\".": "Dạng phủ định là “不是”.",
    "\"谁” can also be pronounced as \"shui”\".": "“谁” cũng có thể đọc là “shuí”.",
    "The word “吗\" is a modal particle typically placed": "“吗” là trợ từ ngữ khí thường đặt cuối câu.",
    "两人一组，用真实姓名对话。": "Hai người một nhóm, dùng tên thật để đối thoại.",
    "没事”。In colloquial speech,": "Trong khẩu ngữ cũng nói “没事” (không sao).",
    "peoplealsosay“没事”or“没事": "Người ta cũng nói “没事”.",
}

OBJ_VI = {
    "pronoun“您\".": "Dùng được đại từ kính ngữ “您”.",
    "understand and use expressions of apology, includi": "Nghe hiểu và dùng câu xin lỗi (ví dụ “对不起”).",
    "respondingwith“没关系”": "Đáp lại xin lỗi bằng “没关系” (không sao).",
    "\"有”’": "Nắm câu với “有” (có).",
}

EXERCISE_FRAG = re.compile(
    r"^([（(]?\d+[）)]|[ABC]\s?|四口人|五口人|两口人|"
    r"杨同乐有一个|杨同乐家有|王一雪有|杨同乐（|）做饭|"
    r"会$|不会$|^B不$|^A会$|^C )"
)


def clean_hanzi(h: str) -> str:
    h = re.sub(r"(Chinese|English).*$", "", h)
    h = re.sub(r"[A-Za-z].*$", "", h) if re.match(r"^[\u4e00-\u9fff“”‘’：:].*[A-Za-z]", h) else h
    # if mixed, take chinese-leading part
    m = re.match(r"^(.*[\u4e00-\u9fff！？。，、：；”’]+)", h)
    if m and re.search(r"[A-Za-z]{3,}", h):
        return m.group(1).strip()
    return h.strip()


def translate(h: str) -> str | None:
    h0 = h.strip()
    if h0 in SENTENCE_VI:
        return SENTENCE_VI[h0]
    c = clean_hanzi(h0)
    if c in SENTENCE_VI:
        return SENTENCE_VI[c]
    if h0 in GRAMMAR_VI:
        return GRAMMAR_VI[h0]
    if c in GRAMMAR_VI:
        return GRAMMAR_VI[c]
    for k, v in OBJ_VI.items():
        if k in h0:
            return v
    for k, v in GRAMMAR_VI.items():
        if k in h0 or h0 in k:
            return v
    for k, v in SENTENCE_VI.items():
        if k in h0 or h0 in k:
            return v
    # patterns
    patterns = [
        (r"^(.+)，你好[!！]?$", lambda m: f"Xin chào {m.group(1)}!"),
        (r"^你好，(.+)[!！]?$", lambda m: f"Xin chào {m.group(1)}!"),
        (r"^我叫(.+)[。.]?$", lambda m: f"Tôi tên {m.group(1)}."),
        (r"^我是(.+)[。.]?$", lambda m: f"Tôi là {m.group(1)}."),
        (r"^这是(.+)[。.]?$", lambda m: f"Đây là {m.group(1)}."),
        (r"^她很(.+)[。.]?$", lambda m: f"Cô ấy rất {m.group(1)}."),
        (r"^他很(.+)[。.]?$", lambda m: f"Anh ấy rất {m.group(1)}."),
        (r"^(.+)吗[？?]?$", lambda m: f"{m.group(1)} phải không?"),
        (r"^请给我(.+)[。.]?$", lambda m: f"Xin cho tôi {m.group(1)}."),
        (r"^我想(.+)[。.]?$", lambda m: f"Tôi muốn {m.group(1)}."),
        (r"^我会(.+)[。.]?$", lambda m: f"Tôi biết/biết cách {m.group(1)}."),
        (r"^我在(.+)[。.]?$", lambda m: f"Tôi ở {m.group(1)}."),
        (r"^今天(.+)[。.]?$", lambda m: f"Hôm nay {m.group(1)}."),
        (r"^明天(.+)[。.]?$", lambda m: f"Ngày mai {m.group(1)}."),
        (r"^昨天(.+)[。.]?$", lambda m: f"Hôm qua {m.group(1)}."),
    ]
    for pat, fn in patterns:
        m = re.match(pat, c)
        if m:
            try:
                return fn(m)
            except Exception:
                pass
    return None


def looks_english(s: str) -> bool:
    return bool(re.search(r"[A-Za-z]", s)) and not re.search(r"[\u4e00-\u9fff]", s)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    db = SessionLocal()
    deleted = updated = 0
    try:
        vocab_vi = {v.hanzi: v.meaning_vi for v in db.query(Vocabulary).all() if v.meaning_vi}

        for it in db.query(LessonItem).all():
            h = (it.hanzi or "").strip()
            vi = (it.meaning_vi or "").strip()

            # delete exercise fragments misclassified as dialogue/sentence
            if it.item_type in ("dialogue_line", "sentence_card", "grammar_tip", "objective"):
                if EXERCISE_FRAG.search(h) or re.match(r"^[ABC]\s*[\u4e00-\u9fff]{0,4}$", h):
                    if "（" in h or re.match(r"^[ABC]", h) or "杨同乐有" in h or "王一雪有" in h:
                        db.delete(it)
                        deleted += 1
                        continue
                if re.match(r"^（\d+）", h) and len(h) < 20:
                    db.delete(it)
                    deleted += 1
                    continue

            changed = False

            # Fix English leaked in meaning_vi
            if vi in EN_LEAK:
                it.meaning_vi = EN_LEAK[vi]
                changed = True
                vi = it.meaning_vi
            elif looks_english(vi) and not vi.startswith(("Nắm", "Có thể", "Hiểu", "Mục tiêu", "Ngữ pháp")):
                # try map or re-translate from hanzi
                low = vi.lower().strip()
                if low in EN_LEAK:
                    it.meaning_vi = EN_LEAK[low]
                    changed = True
                    vi = it.meaning_vi
                else:
                    better = translate(h) or vocab_vi.get(h)
                    if better:
                        it.meaning_vi = better
                        changed = True
                        vi = better

            # Improve weak prefixes
            if vi.startswith(("Câu:", "Lời thoại:", "Từ:", "Ngữ pháp:", "Mục tiêu:", "Chọn nghĩa")):
                better = translate(h) or vocab_vi.get(clean_hanzi(h))
                if not better and it.item_type == "vocab_card":
                    better = vocab_vi.get(h)
                if not better and it.meaning_en and looks_english(it.meaning_en):
                    en = it.meaning_en.strip().lower()
                    better = EN_LEAK.get(en)
                if better:
                    it.meaning_vi = better
                    changed = True
                else:
                    # strip prefix, keep chinese explanation style
                    core = clean_hanzi(h) or h
                    if it.item_type == "grammar_tip" and looks_english(h):
                        it.meaning_vi = "Giải thích ngữ pháp (xem Hán/Anh trong card)."
                        changed = True
                    elif it.item_type == "objective":
                        it.meaning_vi = f"Mục tiêu bài: {core}"
                        changed = True
                    elif it.item_type in ("sentence_card", "dialogue_line"):
                        it.meaning_vi = f"Luyện đọc: {core}"
                        changed = True
                    elif it.item_type == "vocab_card":
                        it.meaning_vi = f"Từ mới: {core}"
                        changed = True

            # Prefer vocab bank for pure vocab
            if it.item_type == "vocab_card" and h in vocab_vi:
                bank_vi = vocab_vi[h]
                if bank_vi and (not it.meaning_vi or looks_english(it.meaning_vi) or it.meaning_vi.startswith("Từ")):
                    # translate bank if english
                    it.meaning_vi = EN_LEAK.get(bank_vi, bank_vi) if looks_english(bank_vi) else bank_vi
                    changed = True

            # Clean hanzi english tails for display
            if h and re.search(r"[\u4e00-\u9fff].*[A-Za-z]{4,}", h):
                cleaned = clean_hanzi(h)
                if cleaned and cleaned != h and len(cleaned) >= 2:
                    it.hanzi = cleaned
                    if it.audio_text and " " in (it.audio_text or ""):
                        it.audio_text = re.sub(r"[^\u4e00-\u9fff，。！？、]", "", cleaned) or cleaned
                    changed = True

            if changed:
                updated += 1

        db.commit()
        weak = 0
        for it in db.query(LessonItem).all():
            vi = it.meaning_vi or ""
            if vi.startswith(("Câu:", "Lời thoại:", "Từ:", "Ngữ pháp:", "Mục tiêu:", "Chọn nghĩa", "Luyện đọc:", "Từ mới:", "Mục tiêu bài:")):
                weak += 1
        print(json.dumps({"deleted": deleted, "updated": updated, "soft_weak_left": weak, "total": db.query(LessonItem).count()}, ensure_ascii=False))
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
