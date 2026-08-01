import json
from pathlib import Path

MEMORY_FILE = Path("memory.json")

if MEMORY_FILE.exists():
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
else:
    memory = {}


def remember(key, value):
    memory[key] = value

    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)


def recall(key):
    return memory.get(key)