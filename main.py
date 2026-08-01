def ai_or_is_it():
    print("AI or is it? 🤖")
    print("Type 'exit' to leave.\n")

    while True:
        user = input("You: ")

        if user.lower() == "exit":
            print("AI: See you later 👋")
            break

        print("AI: Interesting... let me think about that.")

if __name__ == "__main__":
    ai_or_is_it()