"""
Seed vocabulary from Complete HSK Vocabulary (MIT)
https://github.com/drkameleon/complete-hsk-vocabulary
and work scenarios for Tiếng Trung đi làm.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_api = ROOT / "apps" / "api"
if _api.exists():
    sys.path.insert(0, str(_api))
elif (ROOT / "app").exists():
    sys.path.insert(0, str(ROOT))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.models import Scenario, Vocabulary  # noqa: E402

# Image mapper lives next to this script (copied into Docker as /app/scripts)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vocab_images import resolve_image_url  # noqa: E402

HSK_FILE = ROOT / "data" / "hsk-complete.min.json"
VI_FILE = ROOT / "data" / "vi_meanings.json"
LICENSE_NOTE = ROOT / "data" / "HSK_DATASET_LICENSE.txt"
IMAGE_LICENSE_NOTE = ROOT / "data" / "IMAGE_LICENSE.txt"

# Lightweight EN gloss fragment -> VI for MVP (not a full translator)
GLOSS_MAP = {
    "to love": "yêu, thích",
    "to like": "thích",
    "to be fond of": "thích",
    "affection": "tình cảm",
    "I": "tôi",
    "me": "tôi",
    "you": "bạn",
    "he": "anh ấy",
    "she": "cô ấy",
    "we": "chúng tôi",
    "they": "họ",
    "good": "tốt",
    "bad": "xấu",
    "big": "to, lớn",
    "small": "nhỏ",
    "person": "người",
    "people": "mọi người",
    "China": "Trung Quốc",
    "Chinese": "tiếng Trung; người Trung Quốc",
    "work": "làm việc; công việc",
    "company": "công ty",
    "factory": "nhà máy",
    "order": "đơn hàng; lệnh",
    "today": "hôm nay",
    "tomorrow": "ngày mai",
    "yesterday": "hôm qua",
    "time": "thời gian",
    "hour": "giờ",
    "day": "ngày",
    "week": "tuần",
    "month": "tháng",
    "year": "năm",
    "yes": "vâng",
    "no": "không",
    "thank you": "cảm ơn",
    "please": "xin hãy",
    "sorry": "xin lỗi",
    "hello": "xin chào",
    "goodbye": "tạm biệt",
    "eat": "ăn",
    "drink": "uống",
    "see": "nhìn, gặp",
    "look": "nhìn",
    "listen": "nghe",
    "speak": "nói",
    "say": "nói",
    "go": "đi",
    "come": "đến",
    "return": "trở về",
    "buy": "mua",
    "sell": "bán",
    "money": "tiền",
    "job": "việc làm",
    "boss": "sếp",
    "manager": "quản lý",
    "meeting": "cuộc họp",
    "report": "báo cáo",
    "produce": "sản xuất",
    "production": "sản xuất",
    "quality": "chất lượng",
    "check": "kiểm tra",
    "problem": "vấn đề",
    "delay": "trễ, trì hoãn",
    "customer": "khách hàng",
    "supplier": "nhà cung cấp",
}


def en_to_vi(meanings: list[str]) -> str:
    if not meanings:
        return "(chưa có nghĩa)"
    first = meanings[0]
    lower = first.lower().strip()
    for en, vi in GLOSS_MAP.items():
        if lower == en or lower.startswith(en + ";") or lower.startswith(en + ","):
            return vi
    # strip "to " verb marker and keep short gloss as placeholder VI note
    cleaned = re.sub(r"^to\s+", "", first)
    cleaned = cleaned.split(";")[0].strip()
    return cleaned  # temporary: English gloss until curated VI filled


def hsk_level_from_tags(tags: list[str]) -> int | None:
    for level in (1, 2, 3):
        if f"o{level}" in tags:
            return level
    return None


def load_vi_overrides() -> dict[str, str]:
    if VI_FILE.exists():
        return json.loads(VI_FILE.read_text(encoding="utf-8"))
    return {}


SCENARIOS = [
    {
        "track": "work",
        "job_tag": "production",
        "title": "Báo cáo đơn hàng bị trễ",
        "description": "Bạn phải giải thích với sếp Trung Quốc vì sao đơn hàng trễ 2 ngày.",
        "difficulty": 2,
        "starter_lines": ["这个订单怎么还没完成？", "你给我一个准确的交期。"],
        "prompt_system": (
            "You are a strict but fair Chinese factory manager (老板). "
            "Speak only Simplified Chinese in character. "
            "The learner is a Vietnamese employee explaining a 2-day order delay. "
            "Keep replies short (1-2 sentences). Push for cause, new ETA, and prevention. "
            "After each learner message, score grammar/vocabulary/naturalness and suggest a more natural Chinese sentence."
        ),
    },
    {
        "track": "work",
        "job_tag": "office",
        "title": "Ngày đầu đi làm",
        "description": "Tự giới thiệu với chủ quản vào ngày đầu tiên tại công ty Trung Quốc.",
        "difficulty": 1,
        "starter_lines": ["你好，我是你的主管。请先自我介绍一下。"],
        "prompt_system": (
            "You are a friendly Chinese supervisor on the learner's first day. "
            "Speak Simplified Chinese only. Ask about name, role, experience, and goals. "
            "Keep turns short. Score and correct the learner's Chinese after each reply."
        ),
    },
    {
        "track": "work",
        "job_tag": "qc",
        "title": "Gọi QC về lỗi sản phẩm",
        "description": "Báo cáo lỗi chất lượng trên chuyền và đề xuất xử lý.",
        "difficulty": 2,
        "starter_lines": ["质检发现了什么问题？"],
        "prompt_system": (
            "You are a Chinese QC lead. Speak Simplified Chinese. "
            "Ask about defect type, quantity, batch, and corrective action. "
            "Score and rewrite the learner's replies to sound natural in a factory."
        ),
    },
    {
        "track": "work",
        "job_tag": "sales",
        "title": "Thương lượng với khách hàng",
        "description": "Khách muốn giảm giá; bạn giữ biên lợi nhuận hợp lý.",
        "difficulty": 3,
        "starter_lines": ["你们的价格能不能再便宜一点？"],
        "prompt_system": (
            "You are a Chinese customer negotiating price. Speak Simplified Chinese. "
            "Be polite but pushy. React to discounts, MOQ, and lead time. "
            "Score and improve the learner's sales Chinese each turn."
        ),
    },
    {
        "track": "work",
        "job_tag": "it",
        "title": "Báo cáo deploy phiên bản",
        "description": "Thảo luận lịch triển khai bản cập nhật với đồng nghiệp IT Trung Quốc.",
        "difficulty": 2,
        "starter_lines": ["我们什么时候部署这个版本？"],
        "prompt_system": (
            "You are a Chinese IT teammate discussing a software deployment. "
            "Speak Simplified Chinese. Ask about risks, rollback, and schedule. "
            "Score and correct the learner's technical Chinese."
        ),
    },
]

WORK_VOCAB = [
    {
        "hanzi": "订单",
        "traditional": "訂單",
        "pinyin": "dìngdān",
        "meaning_vi": "đơn hàng",
        "meaning_en": "order (purchase/sales)",
        "hsk_level": 3,
        "part_of_speech": "n",
        "frequency": 5000,
        "example_zh": "这个订单什么时候交？",
        "example_vi": "Đơn hàng này khi nào giao?",
    },
    {
        "hanzi": "老板",
        "traditional": "老闆",
        "pinyin": "lǎobǎn",
        "meaning_vi": "sếp, chủ",
        "meaning_en": "boss",
        "hsk_level": 2,
        "part_of_speech": "n",
        "frequency": 4000,
        "example_zh": "老板，我可以请假吗？",
        "example_vi": "Sếp, em xin nghỉ được không?",
    },
    {
        "hanzi": "生产",
        "traditional": "生產",
        "pinyin": "shēngchǎn",
        "meaning_vi": "sản xuất",
        "meaning_en": "to produce; production",
        "hsk_level": 3,
        "part_of_speech": "v",
        "frequency": 3500,
        "example_zh": "生产线今天停了两个小时。",
        "example_vi": "Dây chuyền sản xuất hôm nay dừng hai tiếng.",
    },
    {
        "hanzi": "质检",
        "traditional": "質檢",
        "pinyin": "zhìjiǎn",
        "meaning_vi": "kiểm tra chất lượng (QC)",
        "meaning_en": "quality inspection",
        "hsk_level": 3,
        "part_of_speech": "n",
        "frequency": 8000,
        "example_zh": "质检发现了五个不良品。",
        "example_vi": "QC phát hiện năm sản phẩm lỗi.",
    },
    {
        "hanzi": "部署",
        "traditional": "部署",
        "pinyin": "bùshǔ",
        "meaning_vi": "triển khai / deploy",
        "meaning_en": "to deploy",
        "hsk_level": 3,
        "part_of_speech": "v",
        "frequency": 9000,
        "example_zh": "我们什么时候部署这个版本？",
        "example_vi": "Khi nào chúng ta deploy phiên bản này?",
    },
    {
        "hanzi": "延期",
        "traditional": "延期",
        "pinyin": "yánqī",
        "meaning_vi": "gia hạn, trì hoãn",
        "meaning_en": "to postpone; delay",
        "hsk_level": 3,
        "part_of_speech": "v",
        "frequency": 7000,
        "example_zh": "订单可能会延期两天。",
        "example_vi": "Đơn hàng có thể sẽ trễ hai ngày.",
    },
    {
        "hanzi": "供应商",
        "traditional": "供應商",
        "pinyin": "gōngyìngshāng",
        "meaning_vi": "nhà cung cấp",
        "meaning_en": "supplier",
        "hsk_level": 3,
        "part_of_speech": "n",
        "frequency": 8500,
        "example_zh": "供应商还没到货。",
        "example_vi": "Nhà cung cấp vẫn chưa giao hàng.",
    },
    {
        "hanzi": "请假",
        "traditional": "請假",
        "pinyin": "qǐngjià",
        "meaning_vi": "xin nghỉ",
        "meaning_en": "to ask for leave",
        "hsk_level": 2,
        "part_of_speech": "v",
        "frequency": 6000,
        "example_zh": "我明天想请假一天。",
        "example_vi": "Ngày mai tôi muốn xin nghỉ một ngày.",
    },
]


def ensure_image_column() -> None:
    """Add image_url if missing (Render create_all won't alter existing tables)."""
    from sqlalchemy import text

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE vocabulary ADD COLUMN IF NOT EXISTS image_url VARCHAR(512)"
            )
        )


def seed_vocab(db) -> int:
    if not HSK_FILE.exists():
        raise SystemExit(f"Missing {HSK_FILE}. Download complete.min.json first.")

    ensure_image_column()
    overrides = load_vi_overrides()
    raw = json.loads(HSK_FILE.read_text(encoding="utf-8"))
    existing = {row[0]: row[1] for row in db.query(Vocabulary.hanzi, Vocabulary.id).all()}

    added = 0
    updated_images = 0
    for entry in raw:
        level = hsk_level_from_tags(entry.get("l") or [])
        if level is None:
            continue
        hanzi = entry.get("s")
        if not hanzi:
            continue
        forms = entry.get("f") or [{}]
        form = forms[0] if forms else {}
        info = form.get("i") or {}
        meanings = form.get("m") or []
        meaning_en = "; ".join(meanings) if meanings else None
        meaning_vi = overrides.get(hanzi) or en_to_vi(meanings)
        image_url = resolve_image_url(hanzi, meaning_en, meaning_vi)

        if hanzi in existing:
            if image_url:
                row = db.get(Vocabulary, existing[hanzi])
                if row and row.image_url != image_url:
                    row.image_url = image_url
                    updated_images += 1
            continue

        db.add(
            Vocabulary(
                hanzi=hanzi,
                traditional=form.get("t"),
                pinyin=info.get("y") or info.get("n") or "",
                meaning_vi=meaning_vi,
                meaning_en=meaning_en,
                hsk_level=level,
                part_of_speech=",".join(entry.get("p") or []) or None,
                frequency=entry.get("q"),
                image_url=image_url,
            )
        )
        existing[hanzi] = -1  # mark present
        added += 1
        if added % 100 == 0:
            db.commit()

    for item in WORK_VOCAB:
        image_url = resolve_image_url(
            item["hanzi"], item.get("meaning_en"), item.get("meaning_vi")
        )
        payload = {**item, "image_url": image_url}
        if item["hanzi"] in existing:
            if existing[item["hanzi"]] != -1 and image_url:
                row = db.get(Vocabulary, existing[item["hanzi"]])
                if row and not row.image_url:
                    row.image_url = image_url
                    updated_images += 1
            continue
        db.add(Vocabulary(**payload))
        existing[item["hanzi"]] = -1
        added += 1

    db.commit()
    # Return added; image backfill still happens for existing DBs
    if updated_images and added == 0:
        return updated_images
    return added


def seed_scenarios(db) -> int:
    existing = {s.title for s in db.query(Scenario).all()}
    added = 0
    for sc in SCENARIOS:
        if sc["title"] in existing:
            continue
        db.add(Scenario(**sc))
        added += 1
    db.commit()
    return added


def main() -> None:
    try:
        LICENSE_NOTE.write_text(
            "Vocabulary list derived from Complete HSK Vocabulary (MIT License)\n"
            "https://github.com/drkameleon/complete-hsk-vocabulary\n"
            "Vietnamese meanings curated/adapted for this product; English glosses from CC-CEDICT via upstream.\n",
            encoding="utf-8",
        )
    except OSError:
        pass
    try:
        if IMAGE_LICENSE_NOTE.exists():
            pass  # keep curated license note in repo
    except OSError:
        pass
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        v = seed_vocab(db)
        s = seed_scenarios(db)
        total = db.query(Vocabulary).count()
        print(f"Seeded vocab +{v} (total {total}), scenarios +{s}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
