# ============================================================
# SATURNIA INTENT DETECTOR V1
# ============================================================


def detect_intent(message):

    text = message.lower().strip()

    # -------------------------
    # Coding
    # -------------------------

    coding_phrases = [
        "write code",
        "give me code",
        "write a program",
        "python code",
        "javascript code",
        "debug this",
        "fix this code",
        "program this",
    ]

    if any(phrase in text for phrase in coding_phrases):
        return "coding"

    # -------------------------
    # Explanation
    # -------------------------

    explanation_phrases = [
        "explain",
        "how does",
        "why does",
        "what does",
        "what is",
        "how do",
    ]

    if any(phrase in text for phrase in explanation_phrases):
        return "explanation"

    # -------------------------
    # Conversation
    # -------------------------

    conversation_phrases = [
        "what do you think",
        "do you like",
        "tell me about yourself",
        "are you",
        "how are you",
    ]

    if any(phrase in text for phrase in conversation_phrases):
        return "conversation"

    # -------------------------
    # Default
    # -------------------------

    return "unknown"
