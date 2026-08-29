from app.core.console import safe_print
from app.core.brain import think


def ai_or_is_it():
    safe_print("Hey, there this is a test chatbot")
    safe_print("Type 'exit' to leave.\n")

    while True:
        try:
            user = input("You: ")
        except EOFError:
            safe_print("\nAI: Bye bye")
            break

        if user.lower().strip() == "exit":
            safe_print("AI: Bye bye")
            break

        try:
            response = think(user)
        except Exception as e:
            safe_print("AI: [error]", repr(e))
            continue

        safe_print("AI:", response)


if __name__ == "__main__":
    ai_or_is_it()
