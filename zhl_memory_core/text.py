import re


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?。！？])\s+|\n+")
CHINESE_RE = re.compile(r"[\u4e00-\u9fff]")


def compact_text(text, limit=360):
    value = " ".join((text or "").split())
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def detect_language(text):
    if CHINESE_RE.search(text or ""):
        return "zh-hans"
    return "en"


def sentence_chunks(text):
    chunks = [chunk.strip() for chunk in SENTENCE_SPLIT_RE.split(text or "") if chunk.strip()]
    return chunks or [compact_text(text)]


def normalize_key(text):
    return re.sub(r"[^a-z0-9_]+", "_", text.lower()).strip("_")

