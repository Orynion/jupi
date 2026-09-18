"""
Regression tests for persistent conversation history (Fix #1).

Saturnia's conversation history must survive a process restart:

  - New messages must be persisted via the existing memory system
    (app/core/memory.py -> saturnia_memory.json).
  - A NEW brain module (simulating a new Saturnia process) must load the
    previously persisted conversation history on startup.
  - A missing (or corrupt) persistence file must not crash startup; the
    brain starts with an empty history instead.

Tests are fully isolated from the user's real `saturnia_memory.json`:
every test redirects the memory module's MEMORY_FILE into a temporary
directory that is removed afterwards.

Run with:

    python -m unittest app.core.test_conversation_persistence -v
"""

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class ConversationPersistenceTests(unittest.TestCase):

    def setUp(self):

        # Temporary, isolated memory file for every test.
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.memory_file = Path(self._tmp.name) / "saturnia_memory.json"

        # Redirect the existing memory system to the temp file.
        patcher = patch(
            "app.core.memory.MEMORY_FILE",
            self.memory_file,
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        # Guarantee a GEMINI_API_KEY exists so importing the brain never
        # fails, even on machines without a .env file. load_dotenv() does
        # not override variables already present in the environment.
        env_patcher = patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key-for-persistence-tests"}
        )
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

    def _fresh_brain(self):
        """Import the brain as a brand-new module.

        Removing app.core.brain from sys.modules and re-importing it
        recreates all of the brain's module-level state (including
        conversation_history) from scratch — the closest thing to
        starting a new Saturnia process without actually spawning one.
        """

        sys.modules.pop("app.core.brain", None)

        return importlib.import_module("app.core.brain")

    def _read_persisted_history(self):

        with open(
            self.memory_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return data["conversation_history"]

    # ==========================================================
    # Test A — New conversation is persisted
    # ==========================================================

    def test_new_conversation_is_persisted(self):

        brain = self._fresh_brain()

        self.assertEqual(
            brain.conversation_history,
            []
        )

        # "hello" routes to the greeting path, so no Gemini API call
        # is needed for this test.
        answer = brain.think("hello")

        self.assertTrue(answer)

        persisted = self._read_persisted_history()

        self.assertEqual(
            len(persisted),
            2
        )

        self.assertEqual(
            persisted[0]["role"],
            "user"
        )

        self.assertEqual(
            persisted[0]["text"],
            "hello"
        )

        self.assertEqual(
            persisted[1]["role"],
            "assistant"
        )

        self.assertEqual(
            persisted[1]["text"],
            answer
        )

    # ==========================================================
    # Test B — Reload: a new process recovers the conversation
    # ==========================================================

    def test_new_brain_instance_loads_persisted_history(self):

        # First Saturnia process: hold a conversation.
        first_brain = self._fresh_brain()

        first_answer = first_brain.think("hello")

        # Sanity-check that the first process saw the exchange
        # in its own memory.
        self.assertEqual(
            len(first_brain.conversation_history),
            2
        )

        # Second Saturnia process: a completely fresh brain module
        # that shares no in-memory state with the first one.
        second_brain = self._fresh_brain()

        self.assertIsNot(
            second_brain.conversation_history,
            first_brain.conversation_history
        )

        self.assertEqual(
            len(second_brain.conversation_history),
            2
        )

        self.assertEqual(
            second_brain.conversation_history[0],
            {"role": "user", "text": "hello"}
        )

        self.assertEqual(
            second_brain.conversation_history[1],
            {"role": "assistant", "text": first_answer}
        )

    # ==========================================================
    # Test C — Missing / corrupt persistence does not crash
    # ==========================================================

    def test_missing_persistence_file_starts_empty(self):

        self.assertFalse(self.memory_file.exists())

        brain = self._fresh_brain()

        self.assertEqual(
            brain.conversation_history,
            []
        )

    def test_corrupt_persistence_file_starts_empty(self):

        self.memory_file.write_text(
            "{not valid json",
            encoding="utf-8"
        )

        brain = self._fresh_brain()

        self.assertEqual(
            brain.conversation_history,
            []
        )

    # ==========================================================
    # Test D — Existing memory (facts) behavior still works
    # ==========================================================

    def test_fact_memory_still_persists_between_processes(self):

        first_brain = self._fresh_brain()

        first_brain.think("my name is Dave")

        with open(
            self.memory_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        self.assertEqual(
            data["facts"]["name"]["value"],
            "Dave"
        )

        # A new process must still remember the fact.
        second_brain = self._fresh_brain()

        self.assertEqual(
            second_brain.think("what is my name"),
            "Your name is Dave."
        )

    def test_name_extraction_preserves_capitalization_and_strips_punctuation(self):

        brain = self._fresh_brain()

        for raw_message in [
            "My name is Alex.",
            "My name is Alex!",
            "My name is Alex?",
        ]:
            with self.subTest(raw_message=raw_message):
                brain.think(raw_message)
                self.assertEqual(
                    brain.recall("name"),
                    "Alex"
                )

    def test_name_extraction_is_case_insensitive(self):

        brain = self._fresh_brain()

        for raw_message in [
            "my name is Alex",
            "MY NAME IS Alex",
            "My Name Is Alex",
        ]:
            with self.subTest(raw_message=raw_message):
                brain.think(raw_message)
                self.assertEqual(
                    brain.recall("name"),
                    "Alex"
                )

    # ==========================================================
    # No duplicate conversation entries
    # ==========================================================

    def test_no_duplicate_conversation_entries(self):

        brain = self._fresh_brain()

        brain.think("hello")
        brain.think("hi")

        persisted = self._read_persisted_history()

        # 2 messages per exchange, exactly once each.
        self.assertEqual(
            len(persisted),
            4
        )

        texts = [
            (entry["role"], entry["text"])
            for entry in persisted
        ]

        self.assertEqual(
            len(texts),
            len(set(texts))
        )


if __name__ == "__main__":
    unittest.main()
