from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Entity:
    text: str
    label: str
    start: int
    end: int
    confidence: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class ExtractedFact:
    key: str
    value: Any
    category: str
    sensitivity: str = "private"
    confidence: float = 0.7
    source_text: str = ""
    entities: list[Entity] = field(default_factory=list)

    @property
    def value_text(self):
        if isinstance(self.value, (dict, list)):
            return str(self.value)
        return str(self.value)

    def to_dict(self):
        payload = asdict(self)
        payload["entities"] = [entity.to_dict() for entity in self.entities]
        payload["value_text"] = self.value_text
        return payload


@dataclass(frozen=True)
class MemoryCandidate:
    title: str
    summary: str
    category: str = "other"
    tier: str = "long_term"
    sensitivity: str = "private"
    confidence: float = 0.72
    facts: list[ExtractedFact] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    raw_observation: str = ""
    language: str = ""

    def to_dict(self):
        payload = asdict(self)
        payload["facts"] = [fact.to_dict() for fact in self.facts]
        payload["entities"] = [entity.to_dict() for entity in self.entities]
        return payload


@dataclass(frozen=True)
class NerResult:
    text: str
    language: str
    entities: list[Entity] = field(default_factory=list)
    facts: list[ExtractedFact] = field(default_factory=list)
    memories: list[MemoryCandidate] = field(default_factory=list)
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self):
        return {
            "text": self.text,
            "language": self.language,
            "entities": [entity.to_dict() for entity in self.entities],
            "facts": [fact.to_dict() for fact in self.facts],
            "memories": [memory.to_dict() for memory in self.memories],
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class MemoryEnvelope:
    conversation_text: str
    language: str
    source_channel: str = "sdk"
    source_event_id: str = ""
    memories: list[MemoryCandidate] = field(default_factory=list)
    facts: list[ExtractedFact] = field(default_factory=list)
    entities: list[Entity] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now_iso)

    def to_payload(self):
        return {
            "conversation_text": self.conversation_text,
            "language": self.language,
            "source_channel": self.source_channel,
            "source_event_id": self.source_event_id,
            "memories": [memory.to_dict() for memory in self.memories],
            "facts": [fact.to_dict() for fact in self.facts],
            "entities": [entity.to_dict() for entity in self.entities],
            "metadata": self.metadata,
            "created_at": self.created_at,
        }

