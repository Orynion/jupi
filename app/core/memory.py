memory = {}


def remember(key, value):
    memory[key] = value


def recall(key):
    return memory.get(key)