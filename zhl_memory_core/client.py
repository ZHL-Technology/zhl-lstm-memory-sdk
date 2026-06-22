import json
import os
import platform
import re
import sys
import urllib.error
import urllib.request

from .engine import MemoryEngine

DEFAULT_HTTP_TIMEOUT = 12
DEFAULT_SDK_VERSION = "0.2.4"
SECRET_PATTERNS = [
    re.compile(r"zhlsk_[A-Za-z0-9_\-]+"),
    re.compile(r"zhla_[A-Za-z0-9_\-]+"),
    re.compile(r"(Authorization:\s*Bearer\s+)[A-Za-z0-9_\-\.]+", re.IGNORECASE),
]


class MemoryClientError(RuntimeError):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def redact_secrets(message):
    value = str(message or "")
    for pattern in SECRET_PATTERNS:
        value = pattern.sub(lambda match: f"{match.group(1)}[REDACTED]" if match.lastindex else "[REDACTED]", value)
    return value


def env_timeout(default=DEFAULT_HTTP_TIMEOUT):
    raw_value = os.environ.get("ZHL_MEMORY_HTTP_TIMEOUT_S", "").strip()
    if not raw_value:
        return default
    try:
        return max(1, int(float(raw_value)))
    except ValueError:
        return default


def default_user_agent(sdk_version=DEFAULT_SDK_VERSION):
    system = platform.system() or "UnknownOS"
    machine = platform.machine() or "unknown"
    return f"zhl-memory-core/{sdk_version} ({system}-{machine}; Python {sys.version_info.major}.{sys.version_info.minor})"


class MemoryClient:
    def __init__(
        self,
        base_url,
        api_key,
        device_id,
        device_name="",
        sdk_version=DEFAULT_SDK_VERSION,
        user_agent=None,
        timeout=None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.device_id = device_id
        self.device_name = device_name or platform.node() or "zhl-memory-device"
        self.sdk_version = sdk_version
        self.user_agent = user_agent or os.environ.get("ZHL_MEMORY_USER_AGENT") or default_user_agent(sdk_version)
        self.timeout = timeout if timeout is not None else env_timeout()
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
        try:
            return self._post("/api/v1/memories/ingest/", envelope.to_payload())
        except MemoryClientError as exc:
            if exc.status_code not in {401, 403}:
                raise
            self.activation_token = ""
            self.activate()
            return self._post("/api/v1/memories/ingest/", envelope.to_payload())

    def _post(self, path, payload, include_bearer=True):
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": self.user_agent,
        }
        if include_bearer:
            headers["Authorization"] = f"Bearer {self.activation_token or self.api_key}"
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise MemoryClientError(f"HTTP {exc.code}: {redact_secrets(message)}", status_code=exc.code) from exc
        except urllib.error.URLError as exc:
            raise MemoryClientError(f"Request failed: {redact_secrets(exc.reason)}") from exc
