import re
from dataclasses import dataclass

from .models import Entity, ExtractedFact
from .text import compact_text, detect_language, sentence_chunks


@dataclass(frozen=True)
class Rule:
    key: str
    category: str
    label: str
    pattern: re.Pattern
    sensitivity: str = "private"
    confidence: float = 0.72
    group: str | int = 1


FIRST_NAME_BLOCKLIST = {
    "angry",
    "busy",
    "fine",
    "happy",
    "hungry",
    "ok",
    "okay",
    "ready",
    "sad",
    "sick",
    "sleepy",
    "tired",
}


EN_RULES = [
    Rule("first_name", "identity", "PERSON", re.compile(r"\b(?:my name is|call me)\s+([A-Za-z][a-zA-Z'-]{1,40})(?:\b|$)", re.I), confidence=0.82),
    Rule("first_name", "identity", "PERSON", re.compile(r"\b(?:I am|I'm)\s+([A-Z][a-zA-Z'-]{1,40})(?:\b|$)"), confidence=0.76),
    Rule("last_name", "identity", "PERSON", re.compile(r"\b(?:my last name is|surname is|family name is)\s+([A-Z][a-zA-Z'-]+)", re.I), confidence=0.84),
    Rule("age", "identity", "AGE", re.compile(r"\b(?:i am|i'm)\s+([0-9]{1,3})\s+(?:years old|year old|yo)\b", re.I), confidence=0.88),
    Rule("birth_date", "identity", "DATE", re.compile(r"\b(?:my birthday is|my birth date is|i was born on)\s+([A-Za-z0-9,\-/ ]{4,40})", re.I), confidence=0.78),
    Rule("favorite_color", "preference", "COLOR", re.compile(r"\b(?:my favorite colou?r is|favorite colou?r is|i love the colou?r)\s+([A-Za-z]{3,30})", re.I), confidence=0.84),
    Rule("interest", "preference", "INTEREST", re.compile(r"\b(?:i like|i love|i enjoy|i am interested in)\s+([^.\n!?]{2,140})", re.I), confidence=0.7),
    Rule("dislike", "aversion", "AVERSION", re.compile(r"\b(?:i dislike|i hate|i don't like|i do not like)\s+([^.\n!?]{2,140})", re.I), confidence=0.74),
    Rule("medical_condition", "health", "HEALTH", re.compile(r"\b(?:i have|i suffer from|i was diagnosed with)\s+([^.\n!?]{2,140})", re.I), sensitivity="medical", confidence=0.72),
    Rule("medication", "medication", "MEDICATION", re.compile(r"\b(?:i take|i am taking|my medication is|my medicine is)\s+([^.\n!?]{2,140})", re.I), sensitivity="medical", confidence=0.78),
]

ZH_RULES = [
    Rule("first_name", "identity", "PERSON", re.compile(r"(?:我叫|我的名字是|叫我)([\u4e00-\u9fffA-Za-z]{1,20})"), confidence=0.84),
    Rule("age", "identity", "AGE", re.compile(r"(?:我|今年)([0-9]{1,3})岁"), confidence=0.88),
    Rule("birth_date", "identity", "DATE", re.compile(r"(?:生日是|出生日期是|我出生在)([0-9年月日\-/]{4,20})"), confidence=0.8),
    Rule("favorite_color", "preference", "COLOR", re.compile(r"(?:最喜欢的颜色是|喜欢)(红色|蓝色|绿色|黄色|紫色|黑色|白色|粉色|橙色)"), confidence=0.78),
    Rule("interest", "preference", "INTEREST", re.compile(r"(?:我喜欢|我爱|我感兴趣)([^。！？\n]{2,80})"), confidence=0.7),
    Rule("dislike", "aversion", "AVERSION", re.compile(r"(?:我不喜欢|我讨厌)([^。！？\n]{2,80})"), confidence=0.74),
    Rule("medical_condition", "health", "HEALTH", re.compile(r"(?:我有|我患有)([^。！？\n]{2,80})"), sensitivity="medical", confidence=0.72),
    Rule("medication", "medication", "MEDICATION", re.compile(r"(?:我吃|我正在吃|我的药是)([^。！？\n]{2,80})"), sensitivity="medical", confidence=0.76),
]


def rules_for_language(language):
    if language.startswith("zh"):
        return ZH_RULES
    return EN_RULES


def extract_entities_and_facts(text, language=""):
    language = language or detect_language(text)
    entities = []
    facts = []
    seen_facts = set()

    for rule in rules_for_language(language):
        for match in rule.pattern.finditer(text or ""):
            raw_value = match.group(rule.group).strip(" ,;:，。；：")
            if not raw_value:
                continue
            value = compact_text(raw_value, 240)
            if rule.key == "first_name" and value.casefold() in FIRST_NAME_BLOCKLIST:
                continue
            entity = Entity(
                text=value,
                label=rule.label,
                start=match.start(rule.group),
                end=match.end(rule.group),
                confidence=rule.confidence,
                metadata={"key": rule.key},
            )
            fact_key = (rule.key, value.lower())
            if fact_key in seen_facts:
                continue
            seen_facts.add(fact_key)
            entities.append(entity)
            facts.append(
                ExtractedFact(
                    key=rule.key,
                    value=value,
                    category=rule.category,
                    sensitivity=rule.sensitivity,
                    confidence=rule.confidence,
                    source_text=compact_text(match.group(0), 260),
                    entities=[entity],
                )
            )
    return entities, facts


def extract_story_like_memory(text, language=""):
    chunks = sentence_chunks(text)
    if len(chunks) < 2:
        return None
    lowered = text.lower()
    trigger_words = [
        "remember",
        "accident",
        "when i was",
        "a bad memory",
        "a good memory",
        "trauma",
        "crash",
        "hospital",
        "خاطره",
        "تصادف",
        "بیمارستان",
        "یادم",
        "记得",
        "事故",
    ]
    if not any(word in lowered for word in trigger_words):
        return None
    return compact_text(" ".join(chunks[:3]), 420)
