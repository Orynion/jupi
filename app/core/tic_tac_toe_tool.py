"""Saturnia tool definition for starting the JupiHome Tic-Tac-Toe game."""

from typing import Any, Dict


class TicTacToeTool:
    name = "start_tic_tac_toe"

    description = (
        "Open a Tic-Tac-Toe game in the JupiHome app. Use this when the user "
        "asks to play Tic-Tac-Toe, noughts and crosses, or start a board game."
    )

    def execute(self, parameters: Dict[str, Any] | None = None) -> str:
        """Return the host action understood by JupiHome."""
        return "Tic-Tac-Toe is ready in JupiHome. The user plays X and Saturnia plays O."

    def call(self, **kwargs: Any) -> str:
        return self.execute(kwargs)
