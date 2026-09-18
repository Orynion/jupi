"""Regression tests for the functional coding route."""

import importlib
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


class CodingRouteTests(unittest.TestCase):

    def setUp(self):

        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.memory_file = Path(self._tmp.name) / "saturnia_memory.json"

        self.memory_patcher = patch(
            "app.core.memory.MEMORY_FILE",
            self.memory_file,
        )
        self.memory_patcher.start()
        self.addCleanup(self.memory_patcher.stop)

        self.environment_patcher = patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key-for-coding-route-tests"},
        )
        self.environment_patcher.start()
        self.addCleanup(self.environment_patcher.stop)

        import app.core.brain as brain

        self.brain = importlib.reload(brain)

    def test_coding_route_has_deliberate_gemini_context(self):

        response = SimpleNamespace(text="Use a loop to process the items.")

        with patch.object(
            self.brain.client.models,
            "generate_content",
            return_value=response,
        ) as generate_content:
            answer = self.brain.think("How do I debug this Python bug?")

        self.assertTrue(answer.startswith(response.text))
        generate_content.assert_called_once()
        prompt = generate_content.call_args.kwargs["contents"]
        self.assertIn("CODING REQUEST", prompt)
        self.assertIn("How do I debug this Python bug?", prompt)

    def test_coding_request_uses_existing_response_mechanism(self):

        response = SimpleNamespace(text="Here is the corrected function.")

        with patch.object(
            self.brain.client.models,
            "generate_content",
            return_value=response,
        ) as generate_content:
            answer = self.brain.think("Write Python code to read a file")

        self.assertEqual(answer, response.text)
        generate_content.assert_called_once_with(
            model="gemini-3.1-flash-lite",
            contents=unittest.mock.ANY,
        )

    def test_non_coding_request_keeps_existing_greeting_route(self):

        with patch.object(
            self.brain.client.models,
            "generate_content",
        ) as generate_content:
            answer = self.brain.think("hello")

        self.assertIn(answer, self.brain.GREETINGS)
        generate_content.assert_not_called()


if __name__ == "__main__":
    unittest.main()