"""
Regression tests for the in-memory history cap (Fix #2).

Saturnia's in-memory conversation context must never hold more than
100 individual messages (user and assistant entries are counted
separately, matching the existing representation in brain.py):

  - Fewer than 100 messages: nothing is dropped, ordering is unchanged.
  - Exactly 100 messages: exactly 100 remain.
  - The 101st message: the oldest message is removed.
  - Far more than 100 messages: only the newest 100 remain.

The cap is an in-memory/context limit only. The persistence layer
(app/core/memory.py, from Fix #1) is exercised but not altered; its
own records keep working as before.

Tests are fully isolated from the user's real `saturnia_memory.json`:
every test redirects the memory module's MEMORY_FILE into a temporary
directory that is removed afterwards, and no Gemini API calls are made
(only save_conversation() is exercised directly).

Run with:

    python -m unittest app.core.test_history_cap -v
"""

import importlib
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


class HistoryCapTests(unittest.TestCase):

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
            {"GEMINI_API_KEY": "test-key-for-history-cap-tests"}
        )
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

        # A fresh brain module with an empty (just-loaded) history for
        # every test, so tests never depend on previous test runs.
        self.brain = self._fresh_brain()

    def _fresh_brain(self):
        """Import the brain as a brand-new module.

        Removing app.core.brain from sys.modules and re-importing it
        recreates all of the brain's module-level state (including
        conversation_history) from scratch.
        """

        sys.modules.pop("app.core.brain", None)

        return importlib.import_module("app.core.brain")

    def _add_messages(self, count):
        """Append `count` individual messages via save_conversation().

        Each call to save_conversation() appends exactly two entries
        (one user, one assistant), so count must be even. Texts are
        numbered so ordering and identity are easy to verify.
        """

        for i in range(0, count, 2):

            self.brain.save_conversation(
                f"user message {i}",
                f"assistant message {i + 1}",
            )

    def _message_numbers(self, history):

        return [
            int(entry["text"].rsplit(" ", 1)[1])
            for entry in history
        ]

    # ==========================================================
    # Test A — Under the limit: nothing dropped, order kept
    # ==========================================================

    def test_under_limit_keeps_all_messages_in_order(self):

        self.assertEqual(
            self.brain.MAX_HISTORY_MESSAGES,
            100
        )

        self._add_messages(20)

        history = self.brain.conversation_history

        self.assertEqual(
            len(history),
            20
        )

        # Nothing was dropped: entries 0..19 in original order.
        for i in range(20):

            expected_role = (
                "user" if i % 2 == 0 else "assistant"
            )

            self.assertEqual(
                history[i],
                {
                    "role": expected_role,
                    "text": f"{expected_role} message {i}",
                }
            )

    # ==========================================================
    # Test B — Exactly 100 messages
    # ==========================================================

    def test_exactly_100_messages_are_all_kept(self):

        self._add_messages(100)

        history = self.brain.conversation_history

        self.assertEqual(
            len(history),
            100
        )

        self.assertEqual(
            history[0],
            {"role": "user", "text": "user message 0"}
        )

        self.assertEqual(
            history[-1],
            {
                "role": "assistant",
                "text": "assistant message 99",
            }
        )

    # ==========================================================
    # Test C — The 101st message drops the oldest one
    # ==========================================================

    def test_101st_message_drops_the_oldest(self):

        # 50 exchanges = 100 messages: still exactly at the limit.
        self._add_messages(100)

        self.assertEqual(
            len(self.brain.conversation_history),
            100
        )

        # One more exchange pushes the count to 102 entries.
        self.brain.save_conversation(
            "user message 100",
            "assistant message 101",
        )

        history = self.brain.conversation_history

        self.assertEqual(
            len(history),
            100
        )

        # The two oldest messages (0 and 1) were discarded.
        texts = [entry["text"] for entry in history]

        self.assertNotIn("user message 0", texts)

        self.assertNotIn("assistant message 1", texts)

        # The newest messages are retained at the end.
        self.assertEqual(
            history[-2],
            {"role": "user", "text": "user message 100"}
        )

        self.assertEqual(
            history[-1],
            {
                "role": "assistant",
                "text": "assistant message 101",
            }
        )

        # Ordering is still chronological: message numbers must be
        # strictly increasing across the whole trimmed history.
        numbers = self._message_numbers(history)

        self.assertEqual(
            numbers,
            sorted(numbers)
        )

        self.assertEqual(
            numbers[0],
            2
        )

    # ==========================================================
    # Test D — Many messages: only the newest 100 remain
    # ==========================================================

    def test_many_messages_keep_only_newest_100(self):

        self._add_messages(200)

        history = self.brain.conversation_history

        self.assertEqual(
            len(history),
            100
        )

        # Only the newest 100 messages (numbers 100..199) remain,
        # in the correct (chronological) order.
        self.assertEqual(
            self._message_numbers(history),
            list(range(100, 200))
        )

    # ==========================================================
    # Persistence interaction (Fix #1 must keep working)
    # ==========================================================

    def test_persistence_still_records_capped_messages(self):

        self._add_messages(20)

        self.brain.save_conversation(
            "user message 20",
            "assistant message 21",
        )

        # The in-memory list is capped...
        self.assertLessEqual(
            len(self.brain.conversation_history),
            self.brain.MAX_HISTORY_MESSAGES
        )

        # ...while the persisted file has still received every
        # message written during this session (22 in total — well
        # under the persistence layer's own limit, so nothing is
        # trimmed on disk).
        with open(
            self.memory_file,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        persisted = data["conversation_history"]

        self.assertEqual(
            len(persisted),
            22
        )

        self.assertEqual(
            persisted[-1]["role"],
            "assistant"
        )

        self.assertEqual(
            persisted[-1]["text"],
            "assistant message 21"
        )

        self.assertIn(
            "timestamp",
            persisted[-1]
        )

    def test_reloaded_history_respects_the_cap(self):

        # Fill past the cap in one brain...
        self._add_messages(200)

        # ...persist, then load the history into a brand-new brain
        # (the same path a restarted Saturnia process takes).
        second_brain = self._fresh_brain()

        history = second_brain.conversation_history

        self.assertEqual(
            len(history),
            100
        )

        self.assertEqual(
            self._message_numbers(history),
            list(range(100, 200))
        )


if __name__ == "__main__":
    unittest.main()
