from app.core.brain import think


def ai_or_is_it():
    print("AI or is it? 🤖")
    print("Type 'exit' to leave.\n")

    while True:
        user = input("You: ")

        if user.lower() == "exit":
            print("AI: Goodbye 👋")
            break

        response = think(user)
        print("AI:", response)


if __name__ == "__main__":
    ai_or_is_it()