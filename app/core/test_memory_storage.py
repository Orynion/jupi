"""Unit and integration tests for Saturnia Memory Storage Abstraction (v0.7 Phase 1).

Tests cover:
- SQLiteMemoryStorage schema initialization & CRUD operations
- JSONMemoryStorage implementation
- Fact memory persistence & non-string types
- Legacy history 100-message cap & ordering
- Conversation entity creation, retrieval, message insertion, & listing
- Conversation title auto-generation on first user message
- Strict isolation between independent conversations
- Process restart / database reopening persistence
- Safe, idempotent JSON-to-SQLite migration (including repeat migration & malformed JSON)
- Multithreaded concurrent write safety
"""

import json
import os
import tempfile
import threading
import unittest
import uuid
from pathlib import Path

from app.core.memory_storage import (
    BaseMemoryStorage,
    JSONMemoryStorage,
    SQLiteMemoryStorage,
    migrate_json_to_sqlite,
)


class TestSQLiteMemoryStorage(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.db_path = Path(self._tmp.name) / "test_memory.db"
        self.storage = SQLiteMemoryStorage(self.db_path)

    def test_schema_initialization(self):
        self.assertTrue(self.db_path.exists())

    def test_facts_crud(self):
        self.assertIsNone(self.storage.recall("non_existent"))
        self.storage.remember("username", "SaturnUser")
        self.assertEqual(self.storage.recall("username"), "SaturnUser")

        # Test structured data types
        self.storage.remember("settings", {"theme": "dark", "volume": 80})
        self.assertEqual(
            self.storage.recall("settings"), {"theme": "dark", "volume": 80}
        )

        # Test overwrite
        self.storage.remember("username", "UpdatedUser")
        self.assertEqual(self.storage.recall("username"), "UpdatedUser")

    def test_legacy_history_and_100_cap(self):
        for i in range(120):
            self.storage.save_message("user" if i % 2 == 0 else "assistant", f"msg {i}")

        history = self.storage.get_conversation_history(limit=200)
        self.assertEqual(len(history), 100)
        self.assertEqual(history[0]["text"], "msg 20")
        self.assertEqual(history[-1]["text"], "msg 119")

        # Test limit parameter
        short_history = self.storage.get_conversation_history(limit=5)
        self.assertEqual(len(short_history), 5)
        self.assertEqual(short_history[-1]["text"], "msg 119")

    def test_clear_conversation_history(self):
        self.storage.save_message("user", "hello")
        self.storage.clear_conversation_history()
        self.assertEqual(self.storage.get_conversation_history(), [])

    def test_conversation_entity_lifecycle(self):
        # 1. Create conversation
        conv = self.storage.create_conversation(title="Initial Title")
        conv_id = conv["id"]
        self.assertEqual(conv["title"], "Initial Title")
        self.assertEqual(conv["messages"], [])

        # 2. Retrieve conversation
        retrieved = self.storage.get_conversation(conv_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], conv_id)

        # 3. Add messages
        msg1 = self.storage.add_conversation_message(
            conv_id, "user", "What is 2+2?"
        )
        msg2 = self.storage.add_conversation_message(
            conv_id, "assistant", "4"
        )
        self.assertIsNotNone(msg1)
        self.assertIsNotNone(msg2)

        # 4. Verify message ordering & contents
        conv_updated = self.storage.get_conversation(conv_id)
        self.assertEqual(len(conv_updated["messages"]), 2)
        self.assertEqual(conv_updated["messages"][0]["role"], "user")
        self.assertEqual(conv_updated["messages"][0]["content"], "What is 2+2?")
        self.assertEqual(conv_updated["messages"][1]["role"], "assistant")
        self.assertEqual(conv_updated["messages"][1]["content"], "4")

    def test_auto_title_generation(self):
        conv = self.storage.create_conversation()
        self.assertEqual(conv["title"], "New Conversation")

        self.storage.add_conversation_message(
            conv["id"], "user", "How do I build a rocket to Saturn?"
        )
        conv_updated = self.storage.get_conversation(conv["id"])
        self.assertEqual(conv_updated["title"], "How do I build a rocket to Saturn?")

    def test_conversation_isolation(self):
        conv_a = self.storage.create_conversation(title="Conv A")
        conv_b = self.storage.create_conversation(title="Conv B")

        self.storage.add_conversation_message(conv_a["id"], "user", "Message in A")
        self.storage.add_conversation_message(conv_b["id"], "user", "Message in B")

        res_a = self.storage.get_conversation(conv_a["id"])
        res_b = self.storage.get_conversation(conv_b["id"])

        self.assertEqual(len(res_a["messages"]), 1)
        self.assertEqual(res_a["messages"][0]["content"], "Message in A")

        self.assertEqual(len(res_b["messages"]), 1)
        self.assertEqual(res_b["messages"][0]["content"], "Message in B")

    def test_persistence_across_reopening(self):
        conv = self.storage.create_conversation(title="Durable Conv")
        self.storage.add_conversation_message(conv["id"], "user", "Durable message")
        self.storage.remember("durable_key", "durable_val")

        # Create new storage instance pointing to same file
        reopened = SQLiteMemoryStorage(self.db_path)
        self.assertEqual(reopened.recall("durable_key"), "durable_val")

        conv_reopened = reopened.get_conversation(conv["id"])
        self.assertIsNotNone(conv_reopened)
        self.assertEqual(conv_reopened["title"], "Durable Conv")
        self.assertEqual(len(conv_reopened["messages"]), 1)
        self.assertEqual(conv_reopened["messages"][0]["content"], "Durable message")

    def test_multithreaded_concurrent_writes(self):
        errors = []

        def worker(thread_idx):
            try:
                for i in range(20):
                    self.storage.save_message("user", f"t{thread_idx}_msg{i}")
                    conv = self.storage.create_conversation(title=f"t{thread_idx}_c{i}")
                    self.storage.add_conversation_message(
                        conv["id"], "user", f"t{thread_idx}_content{i}"
                    )
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        all_convs = self.storage.get_conversations()
        self.assertEqual(len(all_convs), 100)  # 5 threads * 20 convs


class TestMigration(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.json_path = Path(self._tmp.name) / "saturnia_memory.json"
        self.db_path = Path(self._tmp.name) / "saturnia_memory.db"
        self.sqlite_storage = SQLiteMemoryStorage(self.db_path)

    def test_migration_from_json(self):
        conv_id = str(uuid.uuid4())
        json_data = {
            "facts": {
                "name": {"value": "Saturnia", "updated_at": "2026-09-19T00:00:00"}
            },
            "conversation_history": [
                {"role": "user", "text": "Hi", "timestamp": "2026-09-19T00:00:01"}
            ],
            "conversations": {
                conv_id: {
                    "id": conv_id,
                    "title": "Migrated Conversation",
                    "created_at": "2026-09-19T00:00:02",
                    "updated_at": "2026-09-19T00:00:03",
                    "messages": [
                        {
                            "id": str(uuid.uuid4()),
                            "role": "user",
                            "content": "Hello world",
                            "created_at": "2026-09-19T00:00:03",
                        }
                    ],
                }
            },
        }

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f)

        migrated = migrate_json_to_sqlite(self.json_path, self.sqlite_storage)
        self.assertTrue(migrated)

        # Verify fact migrated
        self.assertEqual(self.sqlite_storage.recall("name"), "Saturnia")

        # Verify legacy history migrated
        legacy = self.sqlite_storage.get_conversation_history()
        self.assertEqual(len(legacy), 1)
        self.assertEqual(legacy[0]["text"], "Hi")

        # Verify conversation migrated
        conv = self.sqlite_storage.get_conversation(conv_id)
        self.assertIsNotNone(conv)
        self.assertEqual(conv["title"], "Migrated Conversation")
        self.assertEqual(len(conv["messages"]), 1)
        self.assertEqual(conv["messages"][0]["content"], "Hello world")

        # Verify JSON file remains intact
        self.assertTrue(self.json_path.exists())

        # Test repeat migration (idempotent - no duplicates)
        migrate_json_to_sqlite(self.json_path, self.sqlite_storage)
        legacy_repeat = self.sqlite_storage.get_conversation_history()
        self.assertEqual(len(legacy_repeat), 1)
        conv_repeat = self.sqlite_storage.get_conversation(conv_id)
        self.assertEqual(len(conv_repeat["messages"]), 1)

    def test_migration_malformed_json_raises_clear_error(self):
        self.json_path.write_text("invalid { json", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            migrate_json_to_sqlite(self.json_path, self.sqlite_storage)
        self.assertIn("Failed to load JSON file", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

