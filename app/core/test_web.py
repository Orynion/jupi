"""Focused tests for Flask server configuration."""

import os
import unittest
from unittest.mock import patch

from app.core.web import flask_debug_enabled


class FlaskDebugConfigurationTests(unittest.TestCase):

    def assert_debug_value(self, environment_value, expected):
        environment = {} if environment_value is None else {
            "FLASK_DEBUG": environment_value,
        }

        with patch.dict(os.environ, environment, clear=True):
            self.assertEqual(flask_debug_enabled(), expected)

    def test_debug_is_disabled_without_environment_variable(self):
        self.assert_debug_value(None, False)

    def test_debug_accepts_zero_as_false(self):
        self.assert_debug_value("0", False)

    def test_debug_accepts_one_as_true(self):
        self.assert_debug_value("1", True)

    def test_debug_true_value_is_case_insensitive(self):
        self.assert_debug_value("TrUe", True)

    def test_debug_false_value_is_case_insensitive(self):
        self.assert_debug_value("OFF", False)

    def test_unknown_debug_value_is_disabled(self):
        self.assert_debug_value("something-random", False)


if __name__ == "__main__":
    unittest.main()