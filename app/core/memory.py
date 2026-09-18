import json
import os
from pathlib import Path
import threading
import uuid
from datetime import datetime


MEMORY_FILE = Path("saturnia_memory.json")
_memory_lock = threading.RLock()


def _default_memory():
    return {
        "facts": {},
        "conversation_history": [],
        "conversations": {}
    }


def _load_memory():

    with _memory_lock:
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

                if "conversations" not in data:
                    data["conversations"] = {}

                return data

        except Exception:
            return _default_memory()


def _save_memory(data):

    with _memory_lock:
        temp_file = MEMORY_FILE.with_name(
            f"{MEMORY_FILE.stem}_{os.getpid()}_{threading.get_ident()}.tmp"
        )
        try:
            with open(
                temp_file,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )
            os.replace(temp_file, MEMORY_FILE)
        except Exception:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
            raise


# ============================================================
# FACT MEMORY
# ============================================================

def remember(key, value):

    with _memory_lock:
        data = _load_memory()

        data["facts"][key] = {
            "value": value,
            "updated_at": datetime.now().isoformat()
        }

        _save_memory(data)


def recall(key):

    with _memory_lock:
        data = _load_memory()

        item = data["facts"].get(key)

        if not item:
            return None

        return item["value"]


# ============================================================
# CONVERSATION MEMORY (LEGACY / GLOBAL)
# ============================================================

def save_message(role, text):

    with _memory_lock:
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

    with _memory_lock:
        data = _load_memory()

        return data["conversation_history"][-limit:]


def clear_conversation_history():

    with _memory_lock:
        data = _load_memory()

        data["conversation_history"] = []

        _save_memory(data)


# ============================================================
# CONVERSATION ENTITY STORAGE (v1 API)
# ============================================================

def create_conversation(title=None, conversation_id=None):

    with _memory_lock:
        data = _load_memory()

        if conversation_id:
            conv_id = str(uuid.UUID(str(conversation_id)))
        else:
            conv_id = str(uuid.uuid4())

        now = datetime.now().isoformat()
        clean_title = (
            str(title).strip()
            if (title and str(title).strip())
            else "New Conversation"
        )

        conv = {
            "id": conv_id,
            "title": clean_title,
            "created_at": now,
            "updated_at": now,
            "messages": []
        }

        data["conversations"][conv_id] = conv
        _save_memory(data)

        return dict(conv)


def get_conversation(conversation_id):

    with _memory_lock:
        data = _load_memory()
        conv = data.get("conversations", {}).get(str(conversation_id))
        if conv is None:
            return None
        return dict(conv)


def get_conversations():

    with _memory_lock:
        data = _load_memory()
        conversations = data.get("conversations", {})
        summaries = []

        for conv in conversations.values():
            summaries.append({
                "id": conv["id"],
                "title": conv.get("title", "New Conversation"),
                "created_at": conv.get("created_at"),
                "updated_at": conv.get("updated_at"),
                "message_count": len(conv.get("messages", []))
            })

        summaries.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return summaries


def add_conversation_message(conversation_id, role, content):

    with _memory_lock:
        data = _load_memory()
        conv = data.get("conversations", {}).get(str(conversation_id))
        if conv is None:
            return None

        msg_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        message = {
            "id": msg_id,
            "role": role,
            "content": content,
            "created_at": now
        }

        conv.setdefault("messages", []).append(message)

        if conv.get("title") == "New Conversation" and role == "user":
            clean_content = content.strip()
            if clean_content:
                conv["title"] = (
                    clean_content[:50] + "..."
                    if len(clean_content) > 50
                    else clean_content
                )

        conv["updated_at"] = now
        _save_memory(data)

        return dict(message)


# ============================================================
# DEBUG HELPERS
# ============================================================

def get_all_memory():

    with _memory_lock:
        return _load_memory()


def clear_all_memory():

    with _memory_lock:
        _save_memory(
            _default_memory()
        )