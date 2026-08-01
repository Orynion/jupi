def think(message):
    message = message.lower()

    if "hello" in message or "hi" in message:
        return "Hello 👋 I am waking up."

    if "who are you" in message:
        return "I am AI or is it? A small experiment becoming something bigger."

    return "Interesting... I don't know enough yet, but I'm learning."