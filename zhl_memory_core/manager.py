import uuid
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .crypto import dump_state, load_state
from .engine import MemoryEngine


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


SINGLE_VALUE_FACT_KEYS = {"first_name", "last_name", "age", "birth_date"}
FACT_LABELS = {
    "first_name": "name",
    "last_name": "last name",
    "age": "age",
    "birth_date": "birth date",
}


@dataclass
class MemoryManagerResult:
    assistant: str
    language: str = "en"
    saved_count: int = 0
    memory_json: list[dict[str, Any]] | None = None
    candidate_json: dict[str, Any] | None = None
    pending_conflict: bool = False
    created_memories: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return {
            "assistant": self.assistant,
            "language": self.language,
            "saved_count": self.saved_count,
            "memory_json": self.memory_json,
            "candidate_json": self.candidate_json,
            "pending_conflict": self.pending_conflict,
            "created_memories": self.created_memories,
        }


def fact_value_text(fact):
    value = fact.get("value", fact.get("value_text", ""))
    if isinstance(value, (dict, list)):
        return str(value).strip()
    return str(value).strip()


def normalized_value(value):
    return " ".join(str(value or "").split()).casefold()


def meaningful_memories(memories):
    meaningful = []
    for memory in memories or []:
        if memory.get("facts") or memory.get("category") == "story":
            meaningful.append(memory)
    return meaningful


def resolution_intent(message):
    value = (message or "").casefold()
    keep_markers = [
        "both",
        "keep both",
        "two names",
        "two first names",
        "also",
        "nickname",
        "alias",
        "i have two",
        "هر دو",
        "دوتا",
        "دو تا",
        "دو اسم",
        "نام مستعار",
        "لقب",
        "两个",
        "都保留",
        "也叫",
        "都可以",
    ]
    replace_markers = [
        "replace",
        "update",
        "change",
        "correct",
        "real name",
        "not real",
        "wasn't real",
        "wrong",
        "instead",
        "only",
        "جایگزین",
        "عوض",
        "تغییر",
        "واقعی نبود",
        "اشتباه",
        "غلط",
        "اسم واقعی",
        "فقط",
        "替换",
        "更新",
        "改成",
        "不是",
        "真实",
        "错",
    ]
    cancel_markers = ["cancel", "ignore", "forget it", "بیخیال", "لغو", "取消", "算了"]
    if any(marker in value for marker in cancel_markers):
        return "cancel"
    if any(marker in value for marker in keep_markers):
        return "keep_both"
    if any(marker in value for marker in replace_markers):
        return "replace"
    return "unknown"


class MemoryManager:
    def __init__(self, path=None, state=None, default_language="", encryption_key=None):
        self.path = Path(path) if path else None
        self.encryption_key = encryption_key
        self.engine = MemoryEngine(default_language=default_language)
        self.state = deepcopy(state) if state is not None else self._load_state()

    def process(self, text, language="", source_channel="sdk", source_event_id=""):
        text = (text or "").strip()
        if not text:
            return MemoryManagerResult(assistant="Message is required.")

        pending = self.state.get("pending_conflict")
        if pending:
            return self._resolve_pending(text, pending)

        envelope = self.engine.build_envelope(
            text,
            language=language,
            source_channel=source_channel,
            source_event_id=source_event_id,
        )
        payload = envelope.to_payload()
        candidates = meaningful_memories(payload.get("memories", []))
        safe_memories, pending_memories, conflicts = self._split_conflicts(candidates)
        created = self._save_memories(safe_memories, payload) if safe_memories else []
        if pending_memories:
            self.state["pending_conflict"] = {
                "payload": {**payload, "memories": pending_memories, "facts": []},
                "language": payload.get("language", ""),
                "conflicts": conflicts,
            }
            self._persist()

        has_extraction = bool(payload.get("facts") or payload.get("entities") or candidates)
        candidate_json = (
            {
                "facts": payload.get("facts", []),
                "entities": payload.get("entities", []),
                "candidate_memories": candidates,
            }
            if has_extraction
            else None
        )
        language = payload.get("language", "en")
        if pending_memories:
            assistant = self._conflict_question(language, conflicts)
        else:
            assistant = self._assistant_reply(language, payload.get("facts", []), len(created))

        return MemoryManagerResult(
            assistant=assistant,
            language=language,
            saved_count=len(created),
            memory_json=self.memory_json() if created else None,
            candidate_json=candidate_json,
            pending_conflict=bool(pending_memories),
            created_memories=created,
        )

    def memory_json(self, limit=20):
        memories = [
            memory
            for memory in self.state.get("memories", [])
            if memory.get("status", "active") == "active"
        ]
        return list(reversed(memories[-limit:]))

    def current_facts(self):
        return [fact for fact in self.state.get("facts", []) if fact.get("is_current", True)]

    def _default_state(self):
        return {"memories": [], "facts": [], "pending_conflict": None}

    def _load_state(self):
        if not self.path or not self.path.exists():
            return self._default_state()
        try:
            state = load_state(self.path.read_text(encoding="utf-8"), self.encryption_key)
        except ValueError:
            return self._default_state()
        return {
            "memories": list(state.get("memories", [])),
            "facts": list(state.get("facts", [])),
            "pending_conflict": state.get("pending_conflict"),
        }

    def _persist(self):
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(dump_state(self.state, self.encryption_key), encoding="utf-8")

    def _split_conflicts(self, memories):
        safe_memories = []
        pending_memories = []
        conflicts = []
        for memory in memories:
            memory_conflicts = self._conflicts_for_memory(memory)
            if memory_conflicts:
                pending_memories.append(memory)
                conflicts.extend(memory_conflicts)
            else:
                safe_memories.append(memory)
        return safe_memories, pending_memories, conflicts

    def _conflicts_for_memory(self, memory):
        conflicts = []
        for fact in memory.get("facts") or []:
            key = fact.get("key", "")
            if key not in SINGLE_VALUE_FACT_KEYS:
                continue
            value_text = fact_value_text(fact)
            if not value_text:
                continue
            existing_facts = [
                existing
                for existing in self.current_facts()
                if existing.get("key") == key
                and normalized_value(existing.get("value_text")) != normalized_value(value_text)
            ]
            if existing_facts:
                conflicts.append(
                    {
                        "key": key,
                        "label": FACT_LABELS.get(key, key.replace("_", " ")),
                        "new_value": value_text,
                        "existing_values": [fact.get("value_text", "") for fact in existing_facts],
                        "existing_fact_ids": [fact.get("id") for fact in existing_facts],
                    }
                )
        return conflicts

    def _save_memories(self, memories, envelope_payload):
        created = []
        for memory in memories:
            record_id = str(uuid.uuid4())
            record = {
                "id": record_id,
                "title": memory.get("title", "Memory"),
                "summary": memory.get("summary", ""),
                "category": memory.get("category", "other"),
                "tier": memory.get("tier", "long_term"),
                "sensitivity": memory.get("sensitivity", "private"),
                "status": memory.get("status", "active"),
                "confidence": memory.get("confidence", 0.72),
                "key_facts": {"facts": memory.get("facts", [])},
                "entities": memory.get("entities", []),
                "language": memory.get("language", envelope_payload.get("language", "")),
                "source_channel": envelope_payload.get("source_channel", "sdk"),
                "created_at": utc_now_iso(),
                "updated_at": utc_now_iso(),
                "facts": [],
            }
            for fact in memory.get("facts") or []:
                local_fact = {
                    "id": str(uuid.uuid4()),
                    "memory_id": record_id,
                    "key": fact.get("key", "unknown"),
                    "value": fact.get("value", fact.get("value_text", "")),
                    "value_text": fact_value_text(fact),
                    "category": fact.get("category", record["category"]),
                    "sensitivity": fact.get("sensitivity", record["sensitivity"]),
                    "confidence": fact.get("confidence", record["confidence"]),
                    "is_current": True,
                    "last_seen_at": utc_now_iso(),
                }
                self.state.setdefault("facts", []).append(local_fact)
                record["facts"].append(local_fact)
            self.state.setdefault("memories", []).append(record)
            created.append(record)
        self._persist()
        return created

    def _resolve_pending(self, text, pending):
        language = pending.get("language", "en")
        intent = resolution_intent(text)
        if intent == "unknown":
            return MemoryManagerResult(
                assistant=self._resolution_clarifier(language),
                language=language,
                pending_conflict=True,
            )
        if intent == "cancel":
            self.state["pending_conflict"] = None
            self._persist()
            return MemoryManagerResult(
                assistant="No problem. I did not change your memory.",
                language=language,
            )
        if intent == "replace":
            self._archive_conflicting_facts(pending.get("conflicts", []))
        created = self._save_memories(pending["payload"].get("memories", []), pending["payload"])
        self.state["pending_conflict"] = None
        self._persist()
        if language.startswith("zh"):
            assistant = "好的，我已更新记忆。" if intent == "replace" else "好的，我会把两个信息都记住。"
        else:
            assistant = (
                "Got it. I updated the memory."
                if intent == "replace"
                else "Got it. I will keep both details in memory."
            )
        return MemoryManagerResult(
            assistant=assistant,
            language=language,
            saved_count=len(created),
            memory_json=self.memory_json(),
            pending_conflict=False,
            created_memories=created,
        )

    def _archive_conflicting_facts(self, conflicts):
        ids = {
            fact_id
            for conflict in conflicts
            for fact_id in conflict.get("existing_fact_ids", [])
            if fact_id
        }
        memory_ids = set()
        for fact in self.state.get("facts", []):
            if fact.get("id") in ids and fact.get("is_current", True):
                fact["is_current"] = False
                fact["last_seen_at"] = utc_now_iso()
                if fact.get("memory_id"):
                    memory_ids.add(fact["memory_id"])
        for memory in self.state.get("memories", []):
            if memory.get("id") in memory_ids:
                memory["status"] = "archived"
                memory["updated_at"] = utc_now_iso()

    def _conflict_question(self, language, conflicts):
        conflict = conflicts[0]
        existing = ", ".join(conflict["existing_values"])
        label = conflict["label"]
        new_value = conflict["new_value"]
        if language.startswith("zh"):
            return (
                f"我发现这里可能有记忆冲突。之前我记得你的{label}是 {existing}，"
                f"现在你说的是 {new_value}。你想替换旧记录，还是两个都保留？"
            )
        return (
            f"I noticed a possible memory conflict. I previously remembered your {label} as "
            f"{existing}, but now you said {new_value}. Should I replace the old value, or keep both?"
        )

    def _resolution_clarifier(self, language):
        if language.startswith("zh"):
            return "我想谨慎处理记忆。请告诉我是“替换旧记录”，还是“两个都保留”。"
        return "I want to handle this carefully. Please tell me whether to replace the old value or keep both."

    def _assistant_reply(self, language, facts, saved_count):
        if language.startswith("zh"):
            if saved_count:
                return f"好的，我记住了 {saved_count} 条对以后有帮助的信息。"
            if facts:
                return "好的，我听到了。我们可以继续聊。"
            return "好的，我们继续聊。"
        if saved_count:
            return f"Got it. I remembered {saved_count} useful detail(s) for later."
        if facts:
            return "I hear you. We can keep chatting."
        return "Sure, let's keep going."
