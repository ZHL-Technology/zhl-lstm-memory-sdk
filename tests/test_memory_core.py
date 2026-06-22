import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from zhl_memory_core import MemoryEngine, MemoryManager, __version__
from zhl_memory_core.client import MemoryClient, MemoryClientError


class FakeHttpResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


class MemoryCoreTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.2.4")

    def test_core_extracts_private_and_medical_facts(self):
        result = MemoryEngine().analyze("My name is Sara. My favorite color is blue. I take aspirin.")
        keys = {fact.key for fact in result.facts}

        self.assertIn("first_name", keys)
        self.assertIn("favorite_color", keys)
        self.assertIn("medication", keys)

    def test_core_does_not_treat_tired_as_a_name(self):
        result = MemoryEngine().analyze("I am tired. I am Tired.")
        first_names = [fact.value_text for fact in result.facts if fact.key == "first_name"]

        self.assertEqual(first_names, [])

    def test_memory_manager_asks_before_replacing_single_value_fact(self):
        manager = MemoryManager()

        first = manager.process("My name is Ady.", language="en")
        conflict = manager.process("My name is Bob.", language="en")

        self.assertEqual(first.saved_count, 1)
        self.assertTrue(conflict.pending_conflict)
        self.assertEqual(conflict.saved_count, 0)
        self.assertIn("previously remembered", conflict.assistant)
        self.assertEqual([fact["value_text"] for fact in manager.current_facts()], ["Ady"])

        replaced = manager.process("That was not real. Replace it with Bob.")
        current_names = sorted(
            fact["value_text"]
            for fact in manager.current_facts()
            if fact["key"] == "first_name"
        )

        self.assertFalse(replaced.pending_conflict)
        self.assertEqual(current_names, ["Bob"])
        self.assertTrue(any(memory["summary"].endswith("Bob.") for memory in replaced.memory_json))
        self.assertFalse(any(memory["summary"].endswith("Ady.") for memory in replaced.memory_json))

    def test_memory_manager_can_keep_both_single_value_facts(self):
        manager = MemoryManager()

        manager.process("My name is Ady.", language="en")
        conflict = manager.process("My name is Bob.", language="en")
        kept = manager.process("I have two names, keep both.")
        current_names = sorted(
            fact["value_text"]
            for fact in manager.current_facts()
            if fact["key"] == "first_name"
        )

        self.assertTrue(conflict.pending_conflict)
        self.assertFalse(kept.pending_conflict)
        self.assertEqual(current_names, ["Ady", "Bob"])

    def test_memory_manager_persists_local_json(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "memory.json"
            manager = MemoryManager(path=path)
            manager.process("My name is Sara.", language="en")

            restored = MemoryManager(path=path)
            current_names = [
                fact["value_text"]
                for fact in restored.current_facts()
                if fact["key"] == "first_name"
            ]

        self.assertEqual(current_names, ["Sara"])

    def test_memory_manager_can_encrypt_local_state(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "memory.enc"
            manager = MemoryManager(path=path, encryption_key="robot-device-secret")
            manager.process("My name is Sara.", language="en")

            raw_payload = path.read_text(encoding="utf-8")
            restored = MemoryManager(path=path, encryption_key="robot-device-secret")
            current_names = [
                fact["value_text"]
                for fact in restored.current_facts()
                if fact["key"] == "first_name"
            ]

        self.assertTrue(raw_payload.startswith("zhlmem1:"))
        self.assertNotIn("Sara", raw_payload)
        self.assertEqual(current_names, ["Sara"])

    def test_encrypted_local_state_requires_key(self):
        with tempfile.TemporaryDirectory() as tempdir:
            path = Path(tempdir) / "memory.enc"
            MemoryManager(path=path, encryption_key="robot-device-secret").process(
                "My name is Sara.",
                language="en",
            )

            with self.assertRaises(RuntimeError):
                MemoryManager(path=path)


class MemoryClientTests(unittest.TestCase):
    def test_activate_sends_user_agent_and_timeout(self):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append((request, timeout))
            return FakeHttpResponse({"status": "active", "activation_token": "zhla_test_token"})

        client = MemoryClient(
            base_url="https://memory.example.com",
            api_key="zhlsk_test_key",
            device_id="robot-001",
            user_agent="RobotTest/1.0",
            timeout=7,
        )

        with patch("urllib.request.urlopen", fake_urlopen):
            client.activate()

        headers = {name.lower(): value for name, value in calls[0][0].header_items()}
        self.assertEqual(headers["user-agent"], "RobotTest/1.0")
        self.assertEqual(calls[0][1], 7)

    def test_env_overrides_user_agent_and_timeout(self):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append((request, timeout))
            return FakeHttpResponse({"status": "active", "activation_token": "zhla_test_token"})

        with patch.dict(
            os.environ,
            {
                "ZHL_MEMORY_USER_AGENT": "EnvRobot/2.0",
                "ZHL_MEMORY_HTTP_TIMEOUT_S": "9",
            },
        ):
            client = MemoryClient(
                base_url="https://memory.example.com",
                api_key="zhlsk_test_key",
                device_id="robot-001",
            )

        with patch("urllib.request.urlopen", fake_urlopen):
            client.activate()

        headers = {name.lower(): value for name, value in calls[0][0].header_items()}
        self.assertEqual(headers["user-agent"], "EnvRobot/2.0")
        self.assertEqual(calls[0][1], 9)

    def test_ingest_uses_existing_activation_token(self):
        calls = []

        def fake_urlopen(request, timeout):
            calls.append(request)
            return FakeHttpResponse({"created": 1, "memories": []})

        client = MemoryClient(
            base_url="https://memory.example.com",
            api_key="zhlsk_test_key",
            device_id="robot-001",
            user_agent="RobotTest/1.0",
        )
        client.activation_token = "zhla_existing_token"

        with patch("urllib.request.urlopen", fake_urlopen):
            client.ingest("My favorite color is blue.", language="en")

        headers = {name.lower(): value for name, value in calls[0].header_items()}
        self.assertEqual(len(calls), 1)
        self.assertEqual(headers["authorization"], "Bearer zhla_existing_token")
        self.assertEqual(headers["user-agent"], "RobotTest/1.0")

    def test_http_errors_redact_api_key_and_activation_token(self):
        def fake_urlopen(request, timeout):
            raise HTTPError(
                request.full_url,
                403,
                "Forbidden",
                hdrs=None,
                fp=io.BytesIO(
                    b"bad zhlsk_secret_value zhla_secret_token Authorization: Bearer zhla_header_token"
                ),
            )

        client = MemoryClient(
            base_url="https://memory.example.com",
            api_key="zhlsk_secret_value",
            device_id="robot-001",
        )

        with patch("urllib.request.urlopen", fake_urlopen):
            with self.assertRaises(MemoryClientError) as error:
                client.activate()

        message = str(error.exception)
        self.assertEqual(error.exception.status_code, 403)
        self.assertNotIn("zhlsk_secret_value", message)
        self.assertNotIn("zhla_secret_token", message)
        self.assertNotIn("zhla_header_token", message)
        self.assertIn("[REDACTED]", message)


if __name__ == "__main__":
    unittest.main()
