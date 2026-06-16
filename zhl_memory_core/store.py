import json
from pathlib import Path


class LocalMemoryStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, envelope):
        payload = envelope.to_payload() if hasattr(envelope, "to_payload") else envelope
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        return payload

    def iter_recent(self, limit=50):
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        recent = lines[-limit:]
        return [json.loads(line) for line in recent if line.strip()]

    def search(self, query, limit=25):
        query = (query or "").lower()
        matches = []
        for item in reversed(self.iter_recent(limit=500)):
            haystack = json.dumps(item, ensure_ascii=False).lower()
            if query in haystack:
                matches.append(item)
            if len(matches) >= limit:
                break
        return matches

