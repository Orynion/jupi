# ============================================================
# SATURNIA ROUTER V1
# ============================================================


def route(message):

    text = message.lower().strip()

    # -------------------------
    # Greeting
    # -------------------------

    greetings = {
        "hello",
        "hello!",
        "hi",
        "hi!",
        "hey",
        "hey!",
        "hola",
        "hola!",
        "namaste",
        "namaste!",
        "ello",
        "ello!",
        "welcome back",
        "welcome back!",
    }

    if text in greetings:
        return "greeting"

    # -------------------------
    # Memory
    # -------------------------

    if "my name is" in text:
        return "memory"

    if text in {
        "what is my name",
        "what's my name",
    }:
        return "memory"

    # -------------------------
    # Coding
    # -------------------------

    coding_words = [
        "python",
        "code",
        "coding",
        "program",
        "script",
        "debug",
        "bug",
        "error",
    ]

    if any(word in text for word in coding_words):
        return "coding"

    # -------------------------
    # Default
    # -------------------------

    return "conversation"
