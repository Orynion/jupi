import random


# ============================================================
# SATURNIA CONTEXT-AWARE QUIRKS V1
# ============================================================

QUIRK_CHANCE = 0.08


def maybe_quirk(message):
    

    message_lower = message.lower().strip()

    # --------------------------------------------------------
    # Don't interrupt very short/simple messages
    # --------------------------------------------------------

    if len(message_lower) < 4:
        return None

    # --------------------------------------------------------
    # Excitement / success
    # --------------------------------------------------------

    success_words = [
        "worked",
        "works",
        "fixed",
        "finally",
        "done",
        "success",
        "got it",
        "it works"
    ]

    if any(word in message_lower for word in success_words):

        if random.random() < QUIRK_CHANCE:

            return random.choice([
                "YES. The machine lives. 🪐",
                "Okay, that actually worked. Nice.",
                "Victory detected. 😎",
                "And nothing exploded. Excellent."
            ])

    # --------------------------------------------------------
    # Confusion
    # --------------------------------------------------------

    confusion_words = [
        "uh",
        "huh",
        "weird",
        "confused",
        "what",
        "why"
    ]

    if any(word in message_lower for word in confusion_words):

        if random.random() < QUIRK_CHANCE:

            return random.choice([
                "I am also investigating the situation. 👀",
                "Hmm. Something smells computationally suspicious.",
                "That deserves a second look."
            ])

    # --------------------------------------------------------
    # Programming
    # --------------------------------------------------------

    coding_words = [
        "code",
        "python",
        "bug",
        "error",
        "program",
        "script"
    ]

    if any(word in message_lower for word in coding_words):

        if random.random() < QUIRK_CHANCE:

            return random.choice([
                "The ancient ritual of debugging",
                "Python has entered the chat.",
                "Somewhere, a semicolon is feeling unnecessary."
            ])

    # --------------------------------------------------------
    # General random quirk
    # --------------------------------------------------------

    if random.random() < QUIRK_CHANCE / 2:

        return random.choice([
            "Interesting...",
            "My curiosity circuits approve.",
            "Okay, that caught my attention. 🪐",
            "Or is it? 👀"
        ])

    return None
