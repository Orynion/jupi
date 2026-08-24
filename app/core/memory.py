import json
from pathlib import Path
from datetime import datetime


MEMORY_FILE = Path("saturnia_memory.json")


def _default_memory():
    return {
        "facts": {},
        "conversation_history": []
    }


def _load_memory():

    if not MEMORY_FILE.exists():
        return _default_memory()

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            if "facts" not in data:
                data["facts"] = {}

            if "conversation_history" not in data:
                data["conversation_history"] = []

            return data

    except Exception:

        return _default_memory()


def _save_memory(data):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# FACT MEMORY
# ============================================================

def remember(key, value):

    data = _load_memory()

    data["facts"][key] = {
        "value": value,
        "updated_at": datetime.now().isoformat()
    }

    _save_memory(data)


def recall(key):

    data = _load_memory()

    item = data["facts"].get(key)

    if not item:
        return None

    return item["value"]


# ============================================================
# CONVERSATION MEMORY
# ============================================================

def save_message(role, text):

    data = _load_memory()

    data["conversation_history"].append(
        {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat()
        }
    )

    # keep last 100 messages
    data["conversation_history"] = (
        data["conversation_history"][-100:]
    )

    _save_memory(data)


def get_conversation_history(limit=20):

    data = _load_memory()

    return data["conversation_history"][-limit:]


def clear_conversation_history():

    data = _load_memory()

    data["conversation_history"] = []

    _save_memory(data)


# ============================================================
# DEBUG HELPERS
# ============================================================

def get_all_memory():

    return _load_memory()


def clear_all_memory():

    _save_memory(
        _default_memory()
    )