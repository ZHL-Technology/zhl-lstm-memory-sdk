from .models import MemoryCandidate, MemoryEnvelope, NerResult
from .ner import extract_entities_and_facts, extract_story_like_memory
from .text import compact_text, detect_language


class MemoryEngine:
    def __init__(self, default_language=""):
        self.default_language = default_language

    def analyze(self, text, language=""):
        language = language or self.default_language or detect_language(text)
        entities, facts = extract_entities_and_facts(text, language=language)
        memories = [self._memory_from_fact(fact, text, language) for fact in facts]
        story_summary = extract_story_like_memory(text, language=language)
        if story_summary:
            memories.append(
                MemoryCandidate(
                    title="Personal story memory",
                    summary=story_summary,
                    category="story",
                    sensitivity="highly_sensitive",
                    confidence=0.62,
                    facts=[],
                    entities=entities,
                    raw_observation=text,
                    language=language,
                )
            )
        if not memories and text:
            memories.append(
                MemoryCandidate(
                    title="Conversation memory candidate",
                    summary=compact_text(text),
                    category="other",
                    sensitivity="private",
                    confidence=0.38,
                    facts=[],
                    entities=entities,
                    raw_observation=text,
                    language=language,
                )
            )
        return NerResult(
            text=text,
            language=language,
            entities=entities,
            facts=facts,
            memories=memories,
        )

    def build_envelope(self, text, language="", source_channel="sdk", source_event_id="", metadata=None):
        result = self.analyze(text, language=language)
        return MemoryEnvelope(
            conversation_text=text,
            language=result.language,
            source_channel=source_channel,
            source_event_id=source_event_id,
            memories=result.memories,
            facts=result.facts,
            entities=result.entities,
            metadata=metadata or {},
        )

    def _memory_from_fact(self, fact, raw_text, language):
        label = fact.key.replace("_", " ").title()
        return MemoryCandidate(
            title=f"{label}: {fact.value_text}",
            summary=f"{label} is {fact.value_text}.",
            category=fact.category,
            sensitivity=fact.sensitivity,
            confidence=fact.confidence,
            facts=[fact],
            entities=fact.entities,
            raw_observation=raw_text,
            language=language,
        )

