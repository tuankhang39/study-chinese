#!/usr/bin/env python3
"""Enrich HSK1 lesson_items: clean OCR junk, fill VI meanings, translate."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Allow running inside /app
sys.path.insert(0, "/app")

from app.core.database import SessionLocal
from app.models import Lesson, LessonItem, Vocabulary
from app.services.pinyin_util import ensure_pinyin, has_hanzi

ROOT_CANDIDATES = [
    Path("/app/data"),
    Path(__file__).resolve().parents[1] / "data",
]

# English gloss → Vietnamese
EN_VI = {
    "hello": "xin chào",
    "goodbye": "tạm biệt",
    "thank you": "cảm ơn",
    "you're welcome": "không có gì",
    "sorry": "xin lỗi",
    "that's all right": "không sao",
    "never mind": "không sao",
    "it doesn't matter": "không sao",
    "everybody": "mọi người",
    "good; fine": "tốt",
    "good": "tốt",
    "fine": "tốt",
    "student": "học sinh / sinh viên",
    "teacher": "giáo viên",
    "you": "bạn / anh / chị",
    "(plural) you": "các bạn",
    "classmate": "bạn cùng lớp",
    "france": "Pháp",
    "chinese language": "tiếng Trung",
    "thailand": "Thái Lan",
    "cook": "nấu ăn",
    "not; no": "không",
    "be": "là",
    "excuse me": "xin hỏi / xin lỗi",
    "excuseme": "xin hỏi",
    "n.": None,
    "v.": None,
    "adj.": None,
    "pron.": None,
    "adv.": None,
    "num.": None,
    "suf.": None,
}

# Direct Hanzi → VI (beyond bank) for textbook leftovers
HANZI_VI = {
    "你好": "xin chào",
    "您好": "xin chào (kính ngữ)",
    "大家好": "xin chào mọi người",
    "你们好": "xin chào các bạn",
    "老师": "giáo viên",
    "王老师": "cô / thầy Vương",
    "学生": "học sinh / sinh viên",
    "学生们": "các học sinh",
    "同学们": "các bạn cùng lớp",
    "同学": "bạn cùng lớp",
    "大家": "mọi người",
    "你们": "các bạn",
    "我们": "chúng tôi / chúng ta",
    "他们": "họ",
    "她们": "họ (nữ)",
    "们": "hậu tố số nhiều",
    "您": "ngài / bạn (kính ngữ)",
    "你": "bạn",
    "我": "tôi",
    "他": "anh ấy",
    "她": "cô ấy",
    "是": "là",
    "不": "không",
    "很": "rất",
    "也": "cũng",
    "都": "đều",
    "的": "của (trợ từ)",
    "吗": "không? (nghi vấn)",
    "呢": "còn … thì sao?",
    "吧": "nhé / đi (ngữ khí)",
    "了": "rồi (trợ từ)",
    "谢谢": "cảm ơn",
    "不客气": "không có gì",
    "对不起": "xin lỗi",
    "没关系": "không sao",
    "再见": "tạm biệt",
    "请问": "xin hỏi",
    "叫": "gọi là; tên là",
    "姓": "họ",
    "名字": "tên",
    "朋友": "bạn bè",
    "女朋友": "bạn gái",
    "男朋友": "bạn trai",
    "中国": "Trung Quốc",
    "中国人": "người Trung Quốc",
    "法国": "Pháp",
    "法国人": "người Pháp",
    "泰国": "Thái Lan",
    "美国人": "người Mỹ",
    "加拿大": "Canada",
    "中文": "tiếng Trung",
    "汉语": "tiếng Hán",
    "英文": "tiếng Anh",
    "国": "nước, quốc gia",
    "人": "người",
    "有": "có",
    "没有": "không có",
    "个": "cái (loại từ)",
    "两": "hai",
    "二": "hai",
    "三": "ba",
    "四": "bốn",
    "五": "năm",
    "六": "sáu",
    "七": "bảy",
    "八": "tám",
    "九": "chín",
    "十": "mười",
    "多少": "bao nhiêu",
    "什么": "cái gì",
    "谁": "ai",
    "哪": "nào",
    "哪儿": "ở đâu",
    "哪里": "ở đâu",
    "怎么": "thế nào / làm sao",
    "怎么样": "thế nào",
    "几": "mấy",
    "今天": "hôm nay",
    "明天": "ngày mai",
    "昨天": "hôm qua",
    "现在": "bây giờ",
    "上午": "buổi sáng",
    "下午": "buổi chiều",
    "晚上": "buổi tối",
    "点": "giờ; chút",
    "分": "phút",
    "半": "rưỡi",
    "年": "năm",
    "月": "tháng",
    "日": "ngày",
    "号": "số; ngày",
    "星期": "tuần",
    "星期一": "thứ Hai",
    "星期二": "thứ Ba",
    "星期三": "thứ Tư",
    "星期四": "thứ Năm",
    "星期五": "thứ Sáu",
    "星期六": "thứ Bảy",
    "星期日": "Chủ nhật",
    "星期天": "Chủ nhật",
    "今年": "năm nay",
    "岁": "tuổi",
    "工作": "công việc; làm việc",
    "上班": "đi làm",
    "下班": "tan làm",
    "休息": "nghỉ",
    "学习": "học",
    "学校": "trường học",
    "大学": "đại học",
    "医院": "bệnh viện",
    "公司": "công ty",
    "办公室": "văn phòng",
    "家": "nhà",
    "爸爸": "bố",
    "妈妈": "mẹ",
    "哥哥": "anh trai",
    "姐姐": "chị gái",
    "弟弟": "em trai",
    "妹妹": "em gái",
    "儿子": "con trai",
    "女儿": "con gái",
    "孩子": "con / trẻ em",
    "先生": "ông / anh",
    "小姐": "cô",
    "手机": "điện thoại",
    "手机号": "số điện thoại",
    "电话": "điện thoại",
    "号": "số",
    "想": "muốn; nghĩ",
    "会": "biết (kỹ năng); sẽ",
    "能": "có thể",
    "可以": "có thể / được",
    "要": "muốn; cần",
    "在": "ở; đang",
    "有点儿": "hơi",
    "真": "thật",
    "太": "quá",
    "便宜": "rẻ",
    "贵": "đắt",
    "钱": "tiền",
    "块": "đồng (loại từ tiền)",
    "元": "nhân dân tệ",
    "苹果": "táo",
    "茶": "trà",
    "水": "nước",
    "饭": "cơm",
    "菜": "món ăn",
    "吃": "ăn",
    "喝": "uống",
    "看": "xem / nhìn",
    "听": "nghe",
    "说": "nói",
    "读": "đọc",
    "写": "viết",
    "买": "mua",
    "卖": "bán",
    "给": "cho",
    "请": "mời / xin",
    "杯": "cốc",
    "电影": "phim",
    "下雪": "tuyết rơi",
    "冷": "lạnh",
    "热": "nóng",
    "忙": "bận",
    "对": "đúng; đối với",
    "做": "làm",
    "做饭": "nấu ăn",
    "饺子": "há cảo / sủi cảo",
    "一些": "một ít",
    "机场": "sân bay",
    "大兴机场": "sân bay Đại Hưng",
    "售货员": "nhân viên bán hàng",
    "杨同乐": "Dương Đồng Lạc (nhân vật)",
    "王一飞": "Vương Nhất Phi (nhân vật)",
    "王一雪": "Vương Nhất Tuyết (nhân vật)",
    "白家月": "Bạch Gia Nguyệt (nhân vật)",
    "陈天中": "Trần Thiên Trung (nhân vật)",
    "李文": "Lý Văn (nhân vật)",
    "安妮": "Annie (nhân vật)",
    "小语": "Tiểu Ngữ (AI trợ giảng)",
    "刘明": "Lưu Minh (nhân vật)",
}

# Grammar / objective phrase translations
PHRASE_VI = {
    "能听懂并使用礼貌用语打招呼、致谢、告别": "Nghe hiểu và dùng câu lịch sự để chào, cảm ơn, tạm biệt",
    "了解中文交际礼仪，能听懂并使用第二人称代词敬称“您”": "Hiểu nghi thức giao tiếp tiếng Trung; dùng kính ngữ “您”",
    "汉语的基本语序": "Trật tự từ cơ bản trong tiếng Trung",
    "“是”字句": "Câu với động từ “是” (là)",
    "结构助词“的”": "Trợ từ kết cấu “的”",
    "用“吗”的是非问句": "Câu hỏi đúng/sai với “吗”",
    "“有”字句（1）": "Câu với “有” (có) — phần 1",
    "数字的表达": "Cách nói số",
    "语气助词“呢”（1）": "Trợ từ ngữ khí “呢” — phần 1",
    "名量词和名量结构": "Lượng từ danh từ và cấu trúc số + lượng từ",
    "时间的表达（1）": "Cách nói thời gian — phần 1",
    "时间的表达（2）": "Cách nói thời gian — phần 2",
    "名词谓语句": "Câu vị ngữ danh từ",
    "能愿动词“会”": "Động từ năng nguyện “会”",
    "能愿动词“想”": "Động từ năng nguyện “想”",
    "能愿动词“能”": "Động từ năng nguyện “能”",
    "能愿动词“要”": "Động từ năng nguyện “要”",
    "能愿动词“可以”": "Động từ năng nguyện “可以”",
    "连动句（1）": "Câu liên động — phần 1",
    "疑问代词“怎么”": "Đại từ nghi vấn “怎么”",
    "疑问代词“怎么样”": "Đại từ nghi vấn “怎么样”",
    "语气助词“吧”（1）": "Trợ từ ngữ khí “吧” — phần 1",
    "副词、时间词语作状语的位置": "Vị trí trạng ngữ (phó từ / từ thời gian)",
    "方位词": "Từ phương vị",
    "介词“在”": "Giới từ “在”",
    "存现句（1）": "Câu tồn hiện — phần 1",
    "时间词语和处所词语同时作状语的顺序": "Thứ tự trạng ngữ thời gian và nơi chốn",
    "表示序数的“第”": "“第” biểu thị số thứ tự",
    "钱数的表达": "Cách nói số tiền",
    "形容词谓语句": "Câu vị ngữ tính từ",
    "正反问": "Câu hỏi khẳng định–phủ định (A không A)",
    "时间副词“在/正在”": "Phó từ thời gian “在/正在”",
    "非主谓句": "Câu không chủ–vị",
    "语气助词“了（1）”": "Trợ từ ngữ khí “了” — phần 1",
    "“太….…·了”格式": "Cấu trúc “太…了”",
    "“太……了”格式": "Cấu trúc “太…了”",
    "“动词+一下”结构": "Cấu trúc động từ + 一下",
    "双宾语句（1）": "Câu song tân ngữ — phần 1",
    "动态助词“了（2）”": "Trợ từ thể “了” — phần 2",
    "离合词（1）": "Từ ly hợp — phần 1",
    "范围副词“都”": "Phó từ phạm vi “都”",
    "并列复句“…，还/也…”": "Câu ghép song song “…，还/也…”",
    "Basic Word Order in Chinese": "Trật tự từ cơ bản tiếng Trung",
}

JUNK_RE = re.compile(
    r"(朗读对话|Read\s*the\s*dialogue|Role-play|Work in pairs|分角色|"
    r"AI生成合成|New Words|生词|Proper Noun|专有名词|"
    r"On the first day|On campus|Read aloud|大声朗读|"
    r"^\(?\d+\)?$|^[ABC]$|^001$|^002$|^003$)",
    re.I,
)

PINYIN_CLEAN = re.compile(r"[^A-Za-züÜǖǘǚǜāáǎàēéěèīíǐìōóǒòūúǔù\s\-']+")


def data_root() -> Path:
    for p in ROOT_CANDIDATES:
        if p.exists():
            return p
    return Path("/app/data")


def load_vi_bank() -> dict[str, str]:
    bank = dict(HANZI_VI)
    root = data_root()
    vi_path = root / "vi_meanings.json"
    if vi_path.exists():
        bank.update(json.loads(vi_path.read_text(encoding="utf-8")))
    return bank


def clean_pinyin(p: str | None, hanzi: str | None) -> str | None:
    if not p:
        return None
    p = p.strip()
    # OCR often put English meaning into pinyin
    if re.search(r"[\u4e00-\u9fff]", p):
        return None
    if re.search(r"\b(Ms\.|Mr\.|hello|thank|pron|adj|verb|n\.)\b", p, re.I):
        # keep only leading latin-looking pinyin tokens
        m = re.match(r"^([A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔù\s\-']{1,40})", p)
        if m and len(m.group(1).strip()) >= 2 and " " in m.group(1) or re.search(r"[aeiouüāáǎà]", m.group(1), re.I):
            cand = PINYIN_CLEAN.sub("", m.group(1)).strip()
            if cand and not re.search(r"Ms|Mr|hello", cand, re.I):
                return cand[:80]
        return None
    cand = PINYIN_CLEAN.sub("", p).strip()
    return cand[:120] or None


def translate_en(en: str | None) -> str | None:
    if not en:
        return None
    s = en.strip()
    low = re.sub(r"\s+", " ", s.lower())
    if low in EN_VI:
        return EN_VI[low]
    # strip POS tags
    low2 = re.sub(r"^(n\.|v\.|adj\.|adv\.|pron\.|num\.|suf\.)\s*", "", low).strip()
    if low2 in EN_VI:
        return EN_VI[low2]
    # Master the use of ...
    if low.startswith("master"):
        return "Nắm được: " + s
    if low.startswith("be able"):
        return "Có thể: " + s
    if low.startswith("understand"):
        return "Hiểu: " + s
    # If mostly POS junk
    if low in {"n.", "v.", "adj.", "pron.", "adv.", "num.", "suf."}:
        return None
    if re.fullmatch(r"\d+", s):
        return None
    # Keep short English glosses as-is for later, but try simple map words
    return None


def zh_to_vi(text: str, bank: dict[str, str]) -> str | None:
    t = text.strip()
    if not t:
        return None
    # Exact
    if t in bank:
        return bank[t]
    if t in PHRASE_VI:
        return PHRASE_VI[t]
    # Strip English tail
    zh_only = re.sub(r"[A-Za-z].*$", "", t).strip(" .。，,;；")
    if zh_only in bank:
        return bank[zh_only]
    if zh_only in PHRASE_VI:
        return PHRASE_VI[zh_only]
    # Partial phrase match
    for k, v in PHRASE_VI.items():
        if k in t or k in zh_only:
            return v
    # Dialogue-like short sentences — heuristic templates
    templates = [
        (r"^(.+)，你好[!！]?$", r"Xin chào, \1!"),
        (r"^你好，(.+)[!！]?$", r"Xin chào, \1!"),
        (r"^谢谢[!！]?$", "Cảm ơn!"),
        (r"^不客气[!！]?$", "Không có gì!"),
        (r"^对不起[!！]?$", "Xin lỗi!"),
        (r"^没关系[!！]?$", "Không sao!"),
        (r"^再见[!！]?$", "Tạm biệt!"),
        (r"^我叫(.+)$", r"Tôi tên là \1"),
        (r"^我是(.+)$", r"Tôi là \1"),
        (r"^这是(.+)$", r"Đây là \1"),
        (r"^他是(.+)$", r"Anh ấy là \1"),
        (r"^她是(.+)$", r"Cô ấy là \1"),
    ]
    for pat, repl in templates:
        m = re.match(pat, zh_only)
        if m:
            if isinstance(repl, str) and "\\" in repl:
                return m.expand(repl)
            if callable(repl):
                return repl(m)
            return repl if isinstance(repl, str) and "\\" not in repl else m.expand(repl)
    # Word join for short 2-4 char compounds already in bank pieces
    if 1 <= len(zh_only) <= 8 and re.fullmatch(r"[\u4e00-\u9fff，。！？、]+", zh_only):
        # try greedy longest match
        i = 0
        parts = []
        ok = True
        while i < len(zh_only):
            if zh_only[i] in "，。！？、":
                parts.append(zh_only[i])
                i += 1
                continue
            matched = None
            for L in range(min(6, len(zh_only) - i), 0, -1):
                sub = zh_only[i : i + L]
                if sub in bank:
                    matched = bank[sub]
                    i += L
                    break
            if not matched:
                ok = False
                break
            parts.append(matched)
        if ok and parts:
            return " ".join(parts)
    return None


def is_junk(item: LessonItem) -> bool:
    h = (item.hanzi or "").strip()
    if not h:
        return item.item_type != "media"
    if JUNK_RE.search(h):
        return True
    if item.item_type in ("dialogue_line", "sentence_card", "vocab_card"):
        # exercise options like "A两口人" without real vocab intent — keep but translate if possible
        if re.match(r"^[ABC]\s", h) and len(h) < 4:
            return True
        if "AI生成" in h:
            return True
    return False


def enrich_item(item: LessonItem, bank: dict[str, str], vocab_map: dict[str, Vocabulary]) -> bool:
    changed = False
    hanzi = (item.hanzi or "").strip()

    # Clean / generate pinyin for every Chinese item
    if has_hanzi(hanzi):
        py = ensure_pinyin(hanzi, item.pinyin)
        if py and py != (item.pinyin or "").strip():
            item.pinyin = py
            changed = True
    else:
        new_py = clean_pinyin(item.pinyin, hanzi)
        if new_py != item.pinyin and (new_py or item.pinyin):
            if new_py != (item.pinyin or "").strip():
                item.pinyin = new_py
                changed = True

    # Fill from vocab bank first
    if hanzi and hanzi in vocab_map:
        v = vocab_map[hanzi]
        if not (item.meaning_vi or "").strip() and v.meaning_vi:
            item.meaning_vi = v.meaning_vi
            changed = True
        if not (item.pinyin or "").strip() and v.pinyin:
            item.pinyin = v.pinyin
            changed = True
        if not (item.meaning_en or "").strip() and v.meaning_en:
            item.meaning_en = v.meaning_en
            changed = True
        if not (item.audio_text or "").strip():
            item.audio_text = hanzi
            changed = True

    if not (item.meaning_vi or "").strip():
        vi = None
        if hanzi:
            vi = zh_to_vi(hanzi, bank)
        if not vi:
            vi = translate_en(item.meaning_en)
        # For grammar tips that are bilingual lines
        if not vi and hanzi:
            for k, v in PHRASE_VI.items():
                if k in hanzi:
                    vi = v
                    break
        if not vi and item.item_type == "objective" and item.meaning_en:
            vi = translate_en(item.meaning_en) or f"Mục tiêu: {item.meaning_en}"
        if not vi and item.item_type == "media":
            vi = "Bạn đã hoàn thành bài. Hãy ôn flashcard để nhớ lâu hơn."
        if not vi and item.item_type == "quiz_prompt":
            # translate answer option later
            if hanzi:
                vi = zh_to_vi(hanzi, bank) or translate_en(item.meaning_en)
        if vi:
            item.meaning_vi = vi
            changed = True

    # Quiz meta → Vietnamese options/answer
    if item.item_type == "quiz_prompt" and item.meta:
        meta = dict(item.meta)
        ans = meta.get("answer")
        opts = list(meta.get("options") or [])
        new_opts = []
        for o in opts:
            vo = zh_to_vi(str(o), bank) or translate_en(str(o)) or bank.get(str(o))
            # if option is English gloss, translate; if Chinese, translate
            if not vo and re.search(r"[A-Za-z]", str(o)) and not re.search(r"[\u4e00-\u9fff]", str(o)):
                vo = translate_en(str(o)) or str(o)
            if not vo:
                vo = zh_to_vi(str(o), bank) or str(o)
            # Prefer VI for Chinese options via bank
            if re.search(r"[\u4e00-\u9fff]", str(o)):
                vo = zh_to_vi(str(o), bank) or bank.get(str(o)) or str(o)
            new_opts.append(vo)
        new_ans = None
        if ans is not None:
            if re.search(r"[\u4e00-\u9fff]", str(ans)):
                new_ans = zh_to_vi(str(ans), bank) or bank.get(str(ans)) or str(ans)
            else:
                new_ans = translate_en(str(ans)) or zh_to_vi(str(ans), bank) or str(ans)
            # align with options
            if new_ans not in new_opts and str(ans) in opts:
                idx = opts.index(str(ans))
                new_ans = new_opts[idx]
        if new_opts != opts or new_ans != ans:
            meta["options"] = new_opts
            if new_ans is not None:
                meta["answer"] = new_ans
            item.meta = meta
            if not (item.meaning_vi or "").strip() and new_ans:
                item.meaning_vi = str(new_ans)
            changed = True

    if not (item.audio_text or "").strip() and hanzi and re.search(r"[\u4e00-\u9fff]", hanzi):
        # audio = chinese only
        audio = re.sub(r"[^\u4e00-\u9fff，。！？、]", "", hanzi) or hanzi
        item.audio_text = audio[:200]
        changed = True

    return changed


def translate_lesson_titles(db, bank: dict[str, str]) -> int:
    n = 0
    title_map = {
        "AI小语，你好！": "Xin chào AI Tiểu Ngữ!",
        "我叫李文": "Tôi tên Lý Văn",
        "我是中国人": "Tôi là người Trung Quốc",
        "我有两个孩子": "Tôi có hai đứa con",
        "今天我休息": "Hôm nay tôi nghỉ",
        "你的手机号是多少？": "Số điện thoại của bạn là bao nhiêu?",
        "我晚上六点半下班": "Tôi tan làm lúc 6 giờ rưỡi tối",
        "我爸爸也在医院工作": "Bố tôi cũng làm ở bệnh viện",
        "我明天上午在学校学习": "Sáng mai tôi học ở trường",
        "这儿的苹果真便宜！": "Táo ở đây rẻ thật!",
        "我读大学呢": "Tôi đang học đại học",
        "昨天下雪了": "Hôm qua trời có tuyết",
        "请给我一杯茶": "Cho tôi một cốc trà",
        "我看了一个电影": "Tôi đã xem một bộ phim",
        "大兴机场见！": "Gặp nhau ở sân bay Đại Hưng!",
    }
    for L in db.query(Lesson).all():
        vi = title_map.get(L.title_zh) or zh_to_vi(L.title_zh, bank)
        if vi and L.title_vi != vi:
            L.title_vi = vi
            n += 1
        # objectives list
        if L.objectives:
            new_obj = []
            for o in L.objectives:
                s = str(o)
                new_obj.append(zh_to_vi(s, bank) or translate_en(s) or s)
            if new_obj != L.objectives:
                L.objectives = new_obj
                n += 1
        if L.grammar_points:
            new_g = []
            for g in L.grammar_points:
                s = str(g)
                # split "Chinese English"
                zh = re.sub(r"[A-Za-z].*$", "", s).strip()
                vi = PHRASE_VI.get(zh) or PHRASE_VI.get(s) or zh_to_vi(zh or s, bank)
                new_g.append(vi or s)
            if new_g != list(L.grammar_points):
                L.grammar_points = new_g
                n += 1
    return n


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    bank = load_vi_bank()
    db = SessionLocal()
    try:
        vocab_map = {v.hanzi: v for v in db.query(Vocabulary).all()}
        for h, v in vocab_map.items():
            if v.meaning_vi:
                bank.setdefault(h, v.meaning_vi)

        deleted = 0
        updated = 0
        still_miss = 0
        items = db.query(LessonItem).all()
        for it in items:
            if is_junk(it) and it.item_type in ("dialogue_line", "sentence_card", "objective", "grammar_tip"):
                # Soft-clean: convert instruction junk to VI note or delete
                h = (it.hanzi or "")
                if re.search(r"Role-play|分角色|Work in pairs|Read aloud|大声朗读|AI生成合成", h, re.I):
                    db.delete(it)
                    deleted += 1
                    continue
            if enrich_item(it, bank, vocab_map):
                updated += 1
            if it.item_type not in ("media",) and not (it.meaning_vi or "").strip():
                # last resort guess
                h = (it.hanzi or "").strip()
                if h and re.search(r"[\u4e00-\u9fff]", h):
                    # leave Chinese with generic label by type
                    fallback = {
                        "vocab_card": f"Từ: {h}",
                        "sentence_card": f"Câu: {re.sub(r'[A-Za-z].*$', '', h).strip() or h}",
                        "dialogue_line": f"Lời thoại: {re.sub(r'[A-Za-z].*$', '', h).strip() or h}",
                        "grammar_tip": f"Ngữ pháp: {re.sub(r'[A-Za-z].*$', '', h).strip() or h}",
                        "objective": f"Mục tiêu: {re.sub(r'[A-Za-z].*$', '', h).strip() or h}",
                        "quiz_prompt": f"Chọn nghĩa của: {h}",
                    }.get(it.item_type)
                    if fallback:
                        it.meaning_vi = fallback
                        updated += 1
                else:
                    still_miss += 1

        titles = translate_lesson_titles(db, bank)
        db.commit()

        # recount
        miss = (
            db.query(LessonItem)
            .filter(LessonItem.meaning_vi.is_(None) | (LessonItem.meaning_vi == ""))
            .count()
        )
        print(
            json.dumps(
                {
                    "updated_fields": updated,
                    "deleted_junk": deleted,
                    "title_updates": titles,
                    "still_empty_vi": miss,
                    "total_items": db.query(LessonItem).count(),
                },
                ensure_ascii=False,
            )
        )
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
