import tempfile
import unittest
from pathlib import Path

from zhl_memory_core import MemoryEngine, MemoryManager, __version__


class MemoryCoreTests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(__version__, "0.2.2")

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


if __name__ == "__main__":
    unittest.main()
