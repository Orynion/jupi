import random

print("=== AI or is it? ===")

answers = [
    "That's an interesting question.",
    "I think so.",
    "Probably.",
    "I'm not sure.",
    "The answer may surprise you."
]

while True:
    question = input("\nAsk me something (or type quit): ")

    if question.lower() == "quit":
        print("Goodbye.")
        break

    print(random.choice(answers))

    if random.randint(1, 70) == 1:
        print("...or is it?")