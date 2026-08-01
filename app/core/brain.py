from app.core.memory import remember, recall


def think(message):
    message = message.lower()

    if "my name is" in message:
        name = message.replace("my name is", "").strip()
        remember("name", name)
        return f"Nice to meet you, {name}."

    if "what is my name" in message:
        name = recall("name")
        if name:
            return f"Your name is {name}."
        return "I don't know your name yet."

    if "hello" in message or "hi" in message:
        return "Hello 👋 I am waking up."

    if "who are you" in message:
        return "I am AI or is it? A small experiment becoming something bigger."

    return "Interesting... I don't know enough yet, but I'm learning."