import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


class MathSolverLoopTests(unittest.TestCase):

    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key"},
            clear=False,
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        sys.modules.pop("app.core.brain", None)
        self.brain = importlib.import_module("app.core.brain")

    def test_first_solver_succeeds(self):
        with patch.object(self.brain, "route", return_value="math"), \
             patch.object(self.brain, "save_conversation") as save_conversation, \
             patch.object(self.brain, "solve_system", return_value={"answer": "system"}) as system_solver, \
             patch.object(self.brain, "solve_power_root", return_value=None) as power_root_solver, \
             patch.object(self.brain, "solve_quadratic", return_value=None) as quadratic_solver, \
             patch.object(self.brain, "solve_fraction_algebra", return_value=None) as fraction_solver, \
             patch.object(self.brain, "solve_algebra", return_value=None) as algebra_solver, \
             patch.object(self.brain, "solve", return_value=None) as general_solver:

            answer = self.brain.think("2 + 2")

            self.assertEqual(answer, "system")
            system_solver.assert_called_once_with("2 + 2")
            power_root_solver.assert_not_called()
            quadratic_solver.assert_not_called()
            fraction_solver.assert_not_called()
            algebra_solver.assert_not_called()
            general_solver.assert_not_called()
            save_conversation.assert_called_once_with("2 + 2", "system")

    def test_early_solver_returns_none_to_next_solver(self):
        with patch.object(self.brain, "route", return_value="math"), \
             patch.object(self.brain, "save_conversation") as save_conversation, \
             patch.object(self.brain, "solve_system", return_value=None), \
             patch.object(self.brain, "solve_power_root", return_value={"answer": "power"}) as power_solver, \
             patch.object(self.brain, "solve_quadratic", return_value=None) as quadratic_solver, \
             patch.object(self.brain, "solve_fraction_algebra", return_value=None) as fraction_solver, \
             patch.object(self.brain, "solve_algebra", return_value=None) as algebra_solver, \
             patch.object(self.brain, "solve", return_value=None) as general_solver:

            answer = self.brain.think("x^2 = 9")

            self.assertEqual(answer, "power")
            power_solver.assert_called_once_with("x^2 = 9")
            quadratic_solver.assert_not_called()
            fraction_solver.assert_not_called()
            algebra_solver.assert_not_called()
            general_solver.assert_not_called()
            save_conversation.assert_called_once_with("x^2 = 9", "power")

    def test_later_solver_succeeds_after_earlier_none(self):
        with patch.object(self.brain, "route", return_value="math"), \
             patch.object(self.brain, "save_conversation") as save_conversation, \
             patch.object(self.brain, "solve_system", return_value=None), \
             patch.object(self.brain, "solve_power_root", return_value=None), \
             patch.object(self.brain, "solve_quadratic", return_value=None), \
             patch.object(self.brain, "solve_fraction_algebra", return_value=None), \
             patch.object(self.brain, "solve_algebra", return_value={"answer": "algebra"}) as algebra_solver, \
             patch.object(self.brain, "solve", return_value=None) as general_solver:

            answer = self.brain.think("x = 3")

            self.assertEqual(answer, "algebra")
            algebra_solver.assert_called_once_with("x = 3")
            general_solver.assert_not_called()
            save_conversation.assert_called_once_with("x = 3", "algebra")

    def test_no_solver_matches_keeps_general_conversation_flow(self):
        with patch.object(self.brain, "route", return_value="math"), \
             patch.object(self.brain, "save_conversation") as save_conversation, \
             patch.object(self.brain, "solve_system", return_value=None), \
             patch.object(self.brain, "solve_power_root", return_value=None), \
             patch.object(self.brain, "solve_quadratic", return_value=None), \
             patch.object(self.brain, "solve_fraction_algebra", return_value=None), \
             patch.object(self.brain, "solve_algebra", return_value=None), \
             patch.object(self.brain, "solve", return_value=None), \
             patch.object(self.brain.client.models, "generate_content") as generate_content:

            generate_content.return_value = types.SimpleNamespace(
                text="Saturnia: Hello there"
            )

            answer = self.brain.think("What is the weather like?")

            self.assertEqual(answer, "Hello there")
            generate_content.assert_called_once()
            save_conversation.assert_called_once_with("What is the weather like?", "Hello there")


if __name__ == "__main__":
    unittest.main()
