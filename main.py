from app.core.brain import think


def ai_or_is_it():
    print("Hey, there this is a test chatbot")
    print("Type 'exit' to leave.\n")

    while True:
        user = input("You: ")

        if user.lower() == "exit":
            print("AI: Bye bye")
            break

        response = think(user)
        print("AI:", response)


if __name__ == "__main__":
    ai_or_is_it()