"""Focused tests for Saturnia API v1 ("Jupi Everywhere") and backwards compatibility.

Tests cover:
- /api/v1/health
- /api/v1/chat
- backwards compatibility of /api/chat
- conversation retrieval, creation, and listing
- stable UUID conversation IDs (not display names)
- multi-message conversation context continuity
- malformed requests and error handling
- conservative CORS behavior
"""

import json
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.core.web import app


class SaturniaApiV1Tests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

        self.memory_file = Path(self._tmp.name) / "saturnia_memory.json"

        patcher = patch("app.core.memory.MEMORY_FILE", self.memory_file)
        patcher.start()
        self.addCleanup(patcher.stop)

        env_patcher = patch.dict(
            os.environ,
            {"GEMINI_API_KEY": "test-key-for-api-tests"}
        )
        env_patcher.start()
        self.addCleanup(env_patcher.stop)

        app.config["TESTING"] = True
        self.client = app.test_client()

    # ==========================================================
    # Health Endpoint
    # ==========================================================

    def test_health_endpoint_returns_structured_json(self):
        response = self.client.get("/api/v1/health")
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "saturnia")
        self.assertEqual(data.get("version"), "0.65")

    # ==========================================================
    # Versioned Chat (/api/v1/chat)
    # ==========================================================

    def test_v1_chat_creates_conversation_and_returns_stable_id(self):
        # "hello" uses greeting path (local deterministic response)
        payload = {"message": "hello"}
        response = self.client.post(
            "/api/v1/chat",
            json=payload,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)
        self.assertIn("conversation_id", data)

        # Must be valid UUID, not a display name
        conv_id = data["conversation_id"]
        parsed_uuid = uuid.UUID(conv_id)
        self.assertEqual(str(parsed_uuid), conv_id)

    def test_v1_chat_with_existing_conversation_id(self):
        # Create a conversation first
        create_res = self.client.post("/api/v1/conversations", json={"title": "Test Chat"})
        self.assertEqual(create_res.status_code, 201)
        conv_id = create_res.get_json()["id"]

        # Send message to that conversation
        payload = {"message": "hello", "conversation_id": conv_id}
        response = self.client.post(
            "/api/v1/chat",
            json=payload,
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data.get("conversation_id"), conv_id)

        # Verify message persisted in that conversation
        conv_res = self.client.get(f"/api/v1/conversations/{conv_id}")
        self.assertEqual(conv_res.status_code, 200)
        conv_data = conv_res.get_json()
        self.assertEqual(len(conv_data["messages"]), 2)
        self.assertEqual(conv_data["messages"][0]["role"], "user")
        self.assertEqual(conv_data["messages"][0]["content"], "hello")
        self.assertEqual(conv_data["messages"][1]["role"], "assistant")

    # ==========================================================
    # Conversation Context Continuity
    # ==========================================================

    @patch("app.core.brain.client.models.generate_content")
    def test_v1_chat_conversation_context_continuity(self, mock_generate):
        # Simulate Gemini returning contextual replies
        mock_response = MagicMock()
        mock_response.text = "I love blue too!"
        mock_generate.return_value = mock_response

        # Create conversation
        create_res = self.client.post("/api/v1/conversations")
        conv_id = create_res.get_json()["id"]

        # Turn 1: user mentions something
        mock_turn1 = MagicMock()
        mock_turn1.text = "Blue is a peaceful color."
        mock_generate.return_value = mock_turn1

        self.client.post(
            "/api/v1/chat",
            json={"message": "My favorite color is blue", "conversation_id": conv_id}
        )

        # Turn 2: user asks follow-up
        mock_turn2 = MagicMock()
        mock_turn2.text = "Your favorite color is blue."
        mock_generate.return_value = mock_turn2

        self.client.post(
            "/api/v1/chat",
            json={"message": "What is my favorite color?", "conversation_id": conv_id}
        )

        # Inspect the contents argument passed to generate_content on turn 2
        last_call_args = mock_generate.call_args
        prompt_content = last_call_args.kwargs.get("contents") or last_call_args[1].get("contents")
        self.assertIn("My favorite color is blue", prompt_content)
        self.assertIn("Blue is a peaceful color.", prompt_content)
        self.assertIn("What is my favorite color?", prompt_content)

    @patch("app.core.brain.client.models.generate_content")
    def test_v1_conversations_are_strictly_isolated(self, mock_generate):
        mock_response = MagicMock()
        mock_response.text = "Generic response."
        mock_generate.return_value = mock_response

        # Create Conversation A
        res_a = self.client.post("/api/v1/conversations", json={"title": "Topic A"})
        conv_a_id = res_a.get_json()["id"]

        # Create Conversation B
        res_b = self.client.post("/api/v1/conversations", json={"title": "Topic B"})
        conv_b_id = res_b.get_json()["id"]

        # 1. Conversation A -> message
        mock_response.text = "Answer about apples."
        self.client.post(
            "/api/v1/chat",
            json={"message": "I want to discuss apples.", "conversation_id": conv_a_id}
        )

        # 2. Conversation B -> message
        mock_response.text = "Answer about bananas."
        self.client.post(
            "/api/v1/chat",
            json={"message": "I want to discuss bananas.", "conversation_id": conv_b_id}
        )

        # 3. Conversation A -> follow-up
        mock_response.text = "Apples are delicious."
        self.client.post(
            "/api/v1/chat",
            json={"message": "What fruit were we discussing?", "conversation_id": conv_a_id}
        )

        # Verify call args for Conversation A follow-up
        a_followup_call = mock_generate.call_args
        a_prompt = a_followup_call.kwargs.get("contents") or a_followup_call[1].get("contents")

        # Verify A contains A's context
        self.assertIn("apples", a_prompt)
        self.assertIn("Answer about apples.", a_prompt)
        # Verify B's messages do NOT enter A's context
        self.assertNotIn("bananas", a_prompt)
        self.assertNotIn("Answer about bananas.", a_prompt)

        # 4. Conversation B -> follow-up
        mock_response.text = "Bananas are high in potassium."
        self.client.post(
            "/api/v1/chat",
            json={"message": "Can you give nutrition facts for that fruit?", "conversation_id": conv_b_id}
        )

        # Verify call args for Conversation B follow-up
        b_followup_call = mock_generate.call_args
        b_prompt = b_followup_call.kwargs.get("contents") or b_followup_call[1].get("contents")

        # Verify B contains B's context
        self.assertIn("bananas", b_prompt)
        self.assertIn("Answer about bananas.", b_prompt)
        # Verify A's messages do NOT enter B's context
        self.assertNotIn("apples", b_prompt)
        self.assertNotIn("Answer about apples.", b_prompt)

        # 5. Verify that legacy conversation_history remains unpolluted
        with open(self.memory_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("conversation_history"), [])

    # ==========================================================
    # Legacy Chat Backwards Compatibility (/api/chat)
    # ==========================================================

    def test_legacy_api_chat_backwards_compatibility(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "hello"},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertIn("response", data)
        self.assertTrue(len(data["response"]) > 0)
        # Ensure it does not break existing consumers expecting response string
        self.assertIsInstance(data["response"], str)

    def test_legacy_api_chat_empty_message_error(self):
        response = self.client.post(
            "/api/chat",
            json={"message": "   "},
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "Message cannot be empty."})

    def test_legacy_api_chat_no_json_error(self):
        response = self.client.post(
            "/api/chat",
            data="not-json",
            content_type="text/plain"
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {"error": "No JSON data received."})

    # ==========================================================
    # Conversation Endpoints (/api/v1/conversations)
    # ==========================================================

    def test_conversations_crud_endpoints(self):
        # 1. Initially empty
        res = self.client.get("/api/v1/conversations")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json(), {"conversations": []})

        # 2. Create conversation
        res = self.client.post("/api/v1/conversations", json={"title": "Algebra Study"})
        self.assertEqual(res.status_code, 201)
        created = res.get_json()
        self.assertEqual(created["title"], "Algebra Study")
        self.assertEqual(created["messages"], [])
        conv_id = created["id"]
        # Stable UUID check
        self.assertEqual(str(uuid.UUID(conv_id)), conv_id)

        # 3. Retrieve single conversation
        res = self.client.get(f"/api/v1/conversations/{conv_id}")
        self.assertEqual(res.status_code, 200)
        retrieved = res.get_json()
        self.assertEqual(retrieved["id"], conv_id)
        self.assertEqual(retrieved["title"], "Algebra Study")

        # 4. List conversations includes the created conversation
        res = self.client.get("/api/v1/conversations")
        self.assertEqual(res.status_code, 200)
        convs = res.get_json()["conversations"]
        self.assertEqual(len(convs), 1)
        self.assertEqual(convs[0]["id"], conv_id)
        self.assertEqual(convs[0]["message_count"], 0)

    def test_conversations_not_found(self):
        fake_id = str(uuid.uuid4())
        res = self.client.get(f"/api/v1/conversations/{fake_id}")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.get_json(), {"error": "Conversation not found."})

    # ==========================================================
    # Malformed Requests & Error Handling
    # ==========================================================

    def test_v1_chat_missing_json(self):
        res = self.client.post(
            "/api/v1/chat",
            data="raw text",
            content_type="text/plain"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json(), {"error": "No JSON data received."})

    def test_v1_chat_empty_message(self):
        res = self.client.post(
            "/api/v1/chat",
            json={"message": ""},
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json(), {"error": "Message cannot be empty."})

    def test_v1_chat_non_string_message(self):
        res = self.client.post(
            "/api/v1/chat",
            json={"message": 12345},
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.get_json(), {"error": "Message cannot be empty."})

    def test_v1_chat_invalid_conversation_id(self):
        res = self.client.post(
            "/api/v1/chat",
            json={"message": "hello", "conversation_id": "non-existent-id"},
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.get_json(), {"error": "Conversation not found."})

    # ==========================================================
    # Conservative CORS Behavior
    # ==========================================================

    def test_cors_allows_configured_local_origin(self):
        headers = {
            "Origin": "http://localhost:3000",
            "Content-Type": "application/json"
        }
        res = self.client.get("/api/v1/health", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "http://localhost:3000")
        self.assertNotEqual(res.headers.get("Access-Control-Allow-Origin"), "*")

    def test_cors_rejects_untrusted_origin(self):
        headers = {
            "Origin": "http://untrusted-site.example.com",
            "Content-Type": "application/json"
        }
        res = self.client.get("/api/v1/health", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.headers.get("Access-Control-Allow-Origin"))

    def test_cors_preflight_options(self):
        headers = {
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        res = self.client.options("/api/v1/chat", headers=headers)
        self.assertIn(res.status_code, [200, 204])
        self.assertEqual(res.headers.get("Access-Control-Allow-Origin"), "http://localhost:5173")
        self.assertIn("POST", res.headers.get("Access-Control-Allow-Methods", ""))


if __name__ == "__main__":
    unittest.main()
