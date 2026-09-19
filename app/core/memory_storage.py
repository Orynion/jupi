"""Storage abstraction layer for Saturnia memory foundation (v0.7 Phase 1).

Provides:
- BaseMemoryStorage: Abstract base interface for storage backends.
- SQLiteMemoryStorage: Durable, local-first SQLite implementation using built-in sqlite3.
- JSONMemoryStorage: Legacy JSON file storage implementation for backward-compatibility testing.
- migrate_json_to_sqlite: Safe, idempotent migration from saturnia_memory.json to SQLite.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import threading
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional


class BaseMemoryStorage(ABC):
    """Abstract interface for Saturnia memory persistence."""

    @abstractmethod
    def remember(self, key: str, value: Any) -> None:
        """Store a fact key-value pair."""
        pass

    @abstractmethod
    def recall(self, key: str) -> Optional[Any]:
        """Retrieve a stored fact value by key."""
        pass

    @abstractmethod
    def save_message(self, role: str, text: str) -> Dict[str, Any]:
        """Save a message to the legacy global conversation history."""
        pass

    @abstractmethod
    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Retrieve recent legacy global conversation history."""
        pass

    @abstractmethod
    def clear_conversation_history(self) -> None:
        """Clear legacy global conversation history."""
        pass

    @abstractmethod
    def create_conversation(
        self, title: Optional[str] = None, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new v1 conversation entity."""
        pass

    @abstractmethod
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a v1 conversation entity by ID with its messages."""
        pass

    @abstractmethod
    def get_conversations(self) -> List[Dict[str, Any]]:
        """List all v1 conversation summaries ordered by updated_at descending."""
        pass

    @abstractmethod
    def add_conversation_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Add a message to a v1 conversation."""
        pass

    @abstractmethod
    def get_all_memory(self) -> Dict[str, Any]:
        """Return full memory state matching JSON structure."""
        pass

    @abstractmethod
    def clear_all_memory(self) -> None:
        """Reset all memory to empty default state."""
        pass

    def close(self) -> None:
        """Close storage resources if applicable."""
        pass


class SQLiteMemoryStorage(BaseMemoryStorage):
    """Local-first SQLite storage backend using standard library sqlite3."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self._lock = threading.RLock()
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(
            str(self.db_path),
            timeout=10.0,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute("PRAGMA foreign_keys=ON;")
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._lock:
            if not self.db_path.parent.exists():
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS facts (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS legacy_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        role TEXT NOT NULL,
                        text TEXT NOT NULL,
                        timestamp TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    );
                """)
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                    );
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_messages_conv_created
                    ON messages(conversation_id, created_at);
                """)
                conn.commit()

    def remember(self, key: str, value: Any) -> None:
        with self._lock:
            val_str = json.dumps(value) if not isinstance(value, str) else value
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO facts (key, value, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(key) DO UPDATE SET
                        value = excluded.value,
                        updated_at = excluded.updated_at;
                    """,
                    (key, val_str, now),
                )
                conn.commit()

    def recall(self, key: str) -> Optional[Any]:
        with self._lock:
            with self._get_connection() as conn:
                row = conn.execute(
                    "SELECT value FROM facts WHERE key = ?;", (key,)
                ).fetchone()
                if not row:
                    return None
                val_str = row["value"]
                try:
                    return json.loads(val_str)
                except (json.JSONDecodeError, TypeError):
                    return val_str

    def save_message(self, role: str, text: str) -> Dict[str, Any]:
        with self._lock:
            now = datetime.now().isoformat()
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT INTO legacy_history (role, text, timestamp) VALUES (?, ?, ?);",
                    (role, text, now),
                )
                # Maintain legacy 100 message cap
                conn.execute(
                    """
                    DELETE FROM legacy_history
                    WHERE id NOT IN (
                        SELECT id FROM legacy_history ORDER BY id DESC LIMIT 100
                    );
                    """
                )
                conn.commit()
                return {
                    "role": role,
                    "text": text,
                    "timestamp": now,
                }

    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT role, text, timestamp
                    FROM (
                        SELECT role, text, timestamp, id
                        FROM legacy_history
                        ORDER BY id DESC
                        LIMIT ?
                    )
                    ORDER BY id ASC;
                    """,
                    (limit,),
                ).fetchall()
                return [
                    {"role": r["role"], "text": r["text"], "timestamp": r["timestamp"]}
                    for r in rows
                ]

    def clear_conversation_history(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM legacy_history;")
                conn.commit()

    def create_conversation(
        self, title: Optional[str] = None, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
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

            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO conversations (id, title, created_at, updated_at)
                    VALUES (?, ?, ?, ?);
                    """,
                    (conv_id, clean_title, now, now),
                )
                conn.commit()

            return {
                "id": conv_id,
                "title": clean_title,
                "created_at": now,
                "updated_at": now,
                "messages": [],
            }

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            str_id = str(conversation_id)
            with self._get_connection() as conn:
                conv_row = conn.execute(
                    "SELECT id, title, created_at, updated_at FROM conversations WHERE id = ?;",
                    (str_id,),
                ).fetchone()
                if not conv_row:
                    return None

                msg_rows = conn.execute(
                    """
                    SELECT id, role, content, created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC, id ASC;
                    """,
                    (str_id,),
                ).fetchall()

                messages = [
                    {
                        "id": r["id"],
                        "role": r["role"],
                        "content": r["content"],
                        "created_at": r["created_at"],
                    }
                    for r in msg_rows
                ]

                return {
                    "id": conv_row["id"],
                    "title": conv_row["title"],
                    "created_at": conv_row["created_at"],
                    "updated_at": conv_row["updated_at"],
                    "messages": messages,
                }

    def get_conversations(self) -> List[Dict[str, Any]]:
        with self._lock:
            with self._get_connection() as conn:
                rows = conn.execute(
                    """
                    SELECT c.id, c.title, c.created_at, c.updated_at,
                           COUNT(m.id) AS message_count
                    FROM conversations c
                    LEFT JOIN messages m ON c.id = m.conversation_id
                    GROUP BY c.id
                    ORDER BY c.updated_at DESC;
                    """
                ).fetchall()

                return [
                    {
                        "id": r["id"],
                        "title": r["title"],
                        "created_at": r["created_at"],
                        "updated_at": r["updated_at"],
                        "message_count": r["message_count"],
                    }
                    for r in rows
                ]

    def add_conversation_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            str_id = str(conversation_id)
            with self._get_connection() as conn:
                conv_row = conn.execute(
                    "SELECT title FROM conversations WHERE id = ?;", (str_id,)
                ).fetchone()
                if not conv_row:
                    return None

                msg_id = message_id if message_id else str(uuid.uuid4())
                now = created_at if created_at else datetime.now().isoformat()

                conn.execute(
                    """
                    INSERT INTO messages (id, conversation_id, role, content, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        role = excluded.role,
                        content = excluded.content;
                    """,
                    (msg_id, str_id, role, content, now),
                )

                current_title = conv_row["title"]
                if current_title == "New Conversation" and role == "user":
                    clean_content = content.strip()
                    if clean_content:
                        new_title = (
                            clean_content[:50] + "..."
                            if len(clean_content) > 50
                            else clean_content
                        )
                        conn.execute(
                            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?;",
                            (new_title, now, str_id),
                        )
                    else:
                        conn.execute(
                            "UPDATE conversations SET updated_at = ? WHERE id = ?;",
                            (now, str_id),
                        )
                else:
                    conn.execute(
                        "UPDATE conversations SET updated_at = ? WHERE id = ?;",
                        (now, str_id),
                    )

                conn.commit()

                return {
                    "id": msg_id,
                    "role": role,
                    "content": content,
                    "created_at": now,
                }

    def get_all_memory(self) -> Dict[str, Any]:
        with self._lock:
            facts = {}
            with self._get_connection() as conn:
                for row in conn.execute(
                    "SELECT key, value, updated_at FROM facts;"
                ).fetchall():
                    val = row["value"]
                    try:
                        val = json.loads(val)
                    except (json.JSONDecodeError, TypeError):
                        pass
                    facts[row["key"]] = {
                        "value": val,
                        "updated_at": row["updated_at"],
                    }

                legacy = self.get_conversation_history(limit=100)

                conversations = {}
                conv_rows = conn.execute(
                    "SELECT id, title, created_at, updated_at FROM conversations;"
                ).fetchall()
                for crow in conv_rows:
                    cid = crow["id"]
                    m_rows = conn.execute(
                        """
                        SELECT id, role, content, created_at
                        FROM messages
                        WHERE conversation_id = ?
                        ORDER BY created_at ASC, id ASC;
                        """,
                        (cid,),
                    ).fetchall()
                    conversations[cid] = {
                        "id": cid,
                        "title": crow["title"],
                        "created_at": crow["created_at"],
                        "updated_at": crow["updated_at"],
                        "messages": [
                            {
                                "id": m["id"],
                                "role": m["role"],
                                "content": m["content"],
                                "created_at": m["created_at"],
                            }
                            for m in m_rows
                        ],
                    }

                return {
                    "facts": facts,
                    "conversation_history": legacy,
                    "conversations": conversations,
                }

    def clear_all_memory(self) -> None:
        with self._lock:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM messages;")
                conn.execute("DELETE FROM conversations;")
                conn.execute("DELETE FROM legacy_history;")
                conn.execute("DELETE FROM facts;")
                conn.commit()


class JSONMemoryStorage(BaseMemoryStorage):
    """JSON file storage backend preserving original saturnia_memory.json behavior."""

    def __init__(self, json_path: Path):
        self.json_path = Path(json_path)
        self._lock = threading.RLock()

    def _default_memory(self) -> Dict[str, Any]:
        return {"facts": {}, "conversation_history": [], "conversations": {}}

    def _load_memory(self) -> Dict[str, Any]:
        with self._lock:
            if not self.json_path.exists():
                return self._default_memory()
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.setdefault("facts", {})
                    data.setdefault("conversation_history", [])
                    data.setdefault("conversations", {})
                    return data
            except Exception:
                return self._default_memory()

    def _save_memory(self, data: Dict[str, Any]) -> None:
        with self._lock:
            if not self.json_path.parent.exists():
                self.json_path.parent.mkdir(parents=True, exist_ok=True)
            temp_file = self.json_path.with_name(
                f"{self.json_path.stem}_{os.getpid()}_{threading.get_ident()}.tmp"
            )
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
                os.replace(temp_file, self.json_path)
            except Exception:
                if temp_file.exists():
                    try:
                        temp_file.unlink()
                    except OSError:
                        pass
                raise

    def remember(self, key: str, value: Any) -> None:
        with self._lock:
            data = self._load_memory()
            data["facts"][key] = {
                "value": value,
                "updated_at": datetime.now().isoformat(),
            }
            self._save_memory(data)

    def recall(self, key: str) -> Optional[Any]:
        with self._lock:
            data = self._load_memory()
            item = data["facts"].get(key)
            return item["value"] if item else None

    def save_message(self, role: str, text: str) -> Dict[str, Any]:
        with self._lock:
            data = self._load_memory()
            now = datetime.now().isoformat()
            msg = {"role": role, "text": text, "timestamp": now}
            data["conversation_history"].append(msg)
            data["conversation_history"] = data["conversation_history"][-100:]
            self._save_memory(data)
            return msg

    def get_conversation_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._lock:
            data = self._load_memory()
            return data["conversation_history"][-limit:]

    def clear_conversation_history(self) -> None:
        with self._lock:
            data = self._load_memory()
            data["conversation_history"] = []
            self._save_memory(data)

    def create_conversation(
        self, title: Optional[str] = None, conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        with self._lock:
            data = self._load_memory()
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
                "messages": [],
            }
            data["conversations"][conv_id] = conv
            self._save_memory(data)
            return dict(conv)

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._load_memory()
            conv = data.get("conversations", {}).get(str(conversation_id))
            return dict(conv) if conv is not None else None

    def get_conversations(self) -> List[Dict[str, Any]]:
        with self._lock:
            data = self._load_memory()
            conversations = data.get("conversations", {})
            summaries = []
            for conv in conversations.values():
                summaries.append(
                    {
                        "id": conv["id"],
                        "title": conv.get("title", "New Conversation"),
                        "created_at": conv.get("created_at"),
                        "updated_at": conv.get("updated_at"),
                        "message_count": len(conv.get("messages", [])),
                    }
                )
            summaries.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
            return summaries

    def add_conversation_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        message_id: Optional[str] = None,
        created_at: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            data = self._load_memory()
            conv = data.get("conversations", {}).get(str(conversation_id))
            if conv is None:
                return None

            msg_id = message_id if message_id else str(uuid.uuid4())
            now = created_at if created_at else datetime.now().isoformat()
            message = {
                "id": msg_id,
                "role": role,
                "content": content,
                "created_at": now,
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
            self._save_memory(data)
            return dict(message)

    def get_all_memory(self) -> Dict[str, Any]:
        with self._lock:
            return self._load_memory()

    def clear_all_memory(self) -> None:
        with self._lock:
            self._save_memory(self._default_memory())


def migrate_json_to_sqlite(json_path: Path, storage: SQLiteMemoryStorage) -> bool:
    """Migrate data safely and idempotently from saturnia_memory.json to SQLite.

    Preserves the source JSON file intact as a backup.
    Returns True if data was imported, False if json file was missing/empty or invalid.
    """
    json_path = Path(json_path)
    if not json_path.exists():
        return False

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"Failed to load JSON file for migration: {e}") from e

    if not isinstance(data, dict):
        raise ValueError("JSON memory root must be an object/dict")

    # 1. Facts Migration
    facts = data.get("facts", {})
    if isinstance(facts, dict):
        for key, item in facts.items():
            if isinstance(item, dict) and "value" in item:
                val = item["value"]
                if storage.recall(key) is None:
                    storage.remember(key, val)

    # 2. Legacy History Migration
    legacy = data.get("conversation_history", [])
    if isinstance(legacy, list):
        existing_legacy = storage.get_conversation_history(limit=100)
        existing_signatures = {
            (item.get("role"), item.get("text")) for item in existing_legacy
        }
        for item in legacy:
            if isinstance(item, dict):
                role = item.get("role")
                text = item.get("text")
                if role and text and (role, text) not in existing_signatures:
                    storage.save_message(role, text)
                    existing_signatures.add((role, text))

    # 3. Conversations Migration
    conversations = data.get("conversations", {})
    if isinstance(conversations, dict):
        for cid, conv in conversations.items():
            if not isinstance(conv, dict):
                continue
            existing_conv = storage.get_conversation(cid)
            if not existing_conv:
                storage.create_conversation(
                    title=conv.get("title"), conversation_id=cid
                )
                existing_msgs = set()
            else:
                existing_msgs = {m["id"] for m in existing_conv.get("messages", [])}

            messages = conv.get("messages", [])
            if isinstance(messages, list):
                for msg in messages:
                    if isinstance(msg, dict):
                        mid = msg.get("id")
                        role = msg.get("role")
                        content = msg.get("content")
                        created_at = msg.get("created_at")
                        if role and content and (not mid or mid not in existing_msgs):
                            storage.add_conversation_message(
                                cid, role, content, message_id=mid, created_at=created_at
                            )

    return True

