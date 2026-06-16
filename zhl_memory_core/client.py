import json
import platform
import urllib.error
import urllib.request

from .engine import MemoryEngine


class MemoryClientError(RuntimeError):
    pass


class MemoryClient:
    def __init__(self, base_url, api_key, device_id, device_name="", sdk_version="0.2.2"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.device_id = device_id
        self.device_name = device_name or platform.node() or "zhl-memory-device"
        self.sdk_version = sdk_version
        self.engine = MemoryEngine()
        self.activation_token = ""

    def activate(self):
        payload = {
            "api_key": self.api_key,
            "device_id": self.device_id,
            "device_name": self.device_name,
            "sdk_version": self.sdk_version,
            "platform": platform.platform(),
        }
        response = self._post("/api/v1/sdk/activate/", payload, include_bearer=False)
        self.activation_token = response.get("activation_token", "")
        return response

    def analyze(self, text, language=""):
        envelope = self.engine.build_envelope(text, language=language)
        return envelope.to_payload()

    def ingest(self, text, language="", source_channel="sdk", source_event_id=""):
        if not self.activation_token:
            self.activate()
        envelope = self.engine.build_envelope(
            text,
            language=language,
            source_channel=source_channel,
            source_event_id=source_event_id,
            metadata={"device_id": self.device_id},
        )
        return self._post("/api/v1/memories/ingest/", envelope.to_payload())

    def _post(self, path, payload, include_bearer=True):
        data = json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if include_bearer:
            headers["Authorization"] = f"Bearer {self.activation_token or self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise MemoryClientError(f"HTTP {exc.code}: {message}") from exc
