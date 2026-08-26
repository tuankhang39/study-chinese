"""Generate tone-marked pinyin for any Chinese text."""

from __future__ import annotations

import re

from pypinyin import Style, lazy_pinyin

HANZI_RE = re.compile(r"[\u4e00-\u9fff]")
BAD_PINYIN_RE = re.compile(r"[\u4e00-\u9fff]|\b(hello|thank|Ms\.|Mr\.|pron|adj|verb)\b", re.I)


def has_hanzi(text: str | None) -> bool:
    return bool(text and HANZI_RE.search(text))


def to_pinyin(text: str | None) -> str | None:
    if not text or not HANZI_RE.search(text):
        return None

    def _keep(chunk: str) -> list[str]:
        # Keep Latin acronyms / names intact (e.g. AI, HSK)
        return [chunk] if chunk else []

    parts = lazy_pinyin(text, style=Style.TONE, errors=_keep)
    joined = " ".join(str(p) for p in parts if p is not None and str(p) != "")
    joined = re.sub(r"\s+([，。！？、；：,.!?;:…）】」』])", r"\1", joined)
    joined = re.sub(r"([（【「『])\s+", r"\1", joined)
    joined = re.sub(r"\s{2,}", " ", joined).strip()
    return joined[:512] if joined else None


def is_good_pinyin(existing: str | None) -> bool:
    if not existing or not existing.strip():
        return False
    p = existing.strip()
    if BAD_PINYIN_RE.search(p):
        return False
    # Must look like latin syllables / tone marks
    if not re.search(r"[A-Za-züÜāáǎàēéěèīíǐìōóǒòūúǔùǖǘǚǜ]", p):
        return False
    return True


def ensure_pinyin(hanzi: str | None, existing: str | None = None) -> str | None:
    """Return existing pinyin if usable, else generate from hanzi."""
    if is_good_pinyin(existing):
        return existing.strip()[:512]
    return to_pinyin(hanzi)
