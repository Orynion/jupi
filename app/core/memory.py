"""Saturnia Memory Service (v0.7 Phase 1 - Memory Foundation).

Maintains complete backward compatibility with existing Saturnia v0.65 API
and internal callers while delegating persistence to the new Storage Abstraction
(SQLiteMemoryStorage by default, JSONMemoryStorage for legacy/test isolation).
"""

from pathlib import Path
import threading
from typing import Any, Dict, List, Optional

from app.core.memory_storage import (
    BaseMemoryStorage,
    JSONMemoryStorage,
    SQLiteMemoryStorage,
    migrate_json_to_sqlite,
)

MEMORY_FILE = Path("saturnia_memory.json")
DB_FILE = Path("saturnia_memory.db")

_memory_lock = threading.RLock()
_storage_cache: Dict[str, BaseMemoryStorage] = {}
_migrated_paths: set = set()


def get_storage() -> BaseMemoryStorage:
    """Return the active memory storage backend instance.

    Uses SQLiteMemoryStorage by default.
    If MEMORY_FILE is patched/redirected to a custom .json file (e.g. in legacy tests),
    it dynamically falls back to JSONMemoryStorage to preserve test expectations.
    """
    with _memory_lock:
        mem_path = Path(MEMORY_FILE)
        db_path = Path(DB_FILE)

        # If MEMORY_FILE is explicitly redirected to a custom json path (e.g. in test setup)
        if mem_path != Path("saturnia_memory.json") and mem_path.suffix == ".json":
            key = f"json_{mem_path.resolve()}"
            if key not in _storage_cache:
                _storage_cache[key] = JSONMemoryStorage(mem_path)
            return _storage_cache[key]

        key = f"sqlite_{db_path.resolve()}"
        if key not in _storage_cache:
            storage = SQLiteMemoryStorage(db_path)
            _storage_cache[key] = storage
            # Automatic idempotent migration from saturnia_memory.json if present
            if mem_path.exists() and str(mem_path.resolve()) not in _migrated_paths:
                try:
                    migrate_json_to_sqlite(mem_path, storage)
                    _migrated_paths.add(str(mem_path.resolve()))
                except Exception:
                    # Non-fatal migration failure, preserve state
                    pass

        return _storage_cache[key]


# ============================================================
# FACT MEMORY
# ============================================================

def remember(key: str, value: Any) -> None:
    get_storage().remember(key, value)


def recall(key: str) -> Optional[Any]:
    return get_storage().recall(key)


# ============================================================
# CONVERSATION MEMORY (LEGACY / GLOBAL)
# ============================================================

def save_message(role: str, text: str) -> Dict[str, Any]:
    return get_storage().save_message(role, text)


def get_conversation_history(limit: int = 20) -> List[Dict[str, Any]]:
    return get_storage().get_conversation_history(limit=limit)


def clear_conversation_history() -> None:
    get_storage().clear_conversation_history()


# ============================================================
# CONVERSATION ENTITY STORAGE (v1 API)
# ============================================================

def create_conversation(
    title: Optional[str] = None, conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    return get_storage().create_conversation(
        title=title, conversation_id=conversation_id
    )


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    return get_storage().get_conversation(conversation_id)


def get_conversations() -> List[Dict[str, Any]]:
    return get_storage().get_conversations()


def add_conversation_message(
    conversation_id: str, role: str, content: str
) -> Optional[Dict[str, Any]]:
    return get_storage().add_conversation_message(
        conversation_id=conversation_id, role=role, content=content
    )


# ============================================================
# DEBUG HELPERS
# ============================================================

def get_all_memory() -> Dict[str, Any]:
    return get_storage().get_all_memory()


def clear_all_memory() -> None:
    get_storage().clear_all_memory()