
from app.core.math_engine import solve


tests = [
    "25 * 17",
    "What is 25% of 800?",
    "What is 3/4 of 100?",
    "What is the average of 10, 20, 30?",
    "Is 75 greater than 42?",
]


for question in tests:
    print("\nQuestion:", question)
    print(solve(question))
