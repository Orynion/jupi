"""Version 1 API blueprint for Saturnia ("Jupi Everywhere").

Provides client-neutral endpoints for health checks, versioned chat,
and conversation management.
"""

from flask import Blueprint, jsonify, request

from app.core.brain import think
from app.core.memory import (
    create_conversation,
    get_conversation,
    get_conversations,
)

api_v1 = Blueprint("api_v1", __name__, url_prefix="/api/v1")


@api_v1.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "saturnia",
        "version": "0.65"
    }), 200

@api_v1.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):
        return jsonify({
            "error": "No JSON data received."
        }), 400

    raw_message = data.get("message")
    if not isinstance(raw_message, str):
        return jsonify({
            "error": "Message cannot be empty."
        }), 400

    message = raw_message.strip()
    if not message:
        return jsonify({
            "error": "Message cannot be empty."
        }), 400

    conversation_id = data.get("conversation_id")

    if conversation_id:
        conversation_id = str(conversation_id).strip()
        existing = get_conversation(conversation_id)
        if not existing:
            return jsonify({
                "error": "Conversation not found."
            }), 404
    else:
        new_conv = create_conversation()
        conversation_id = new_conv["id"]

    response = think(message, conversation_id=conversation_id)

    return jsonify({
        "response": response,
        "conversation_id": conversation_id
    }), 200


@api_v1.route("/conversations", methods=["GET"])
def list_conversations():
    conversations = get_conversations()
    return jsonify({
        "conversations": conversations
    }), 200


@api_v1.route("/conversations", methods=["POST"])
def new_conversation():
    data = request.get_json(silent=True) or {}

    title = None
    if isinstance(data, dict):
        raw_title = data.get("title")
        if isinstance(raw_title, str) and raw_title.strip():
            title = raw_title.strip()

    conv = create_conversation(title=title)
    return jsonify(conv), 201


@api_v1.route("/conversations/<conversation_id>", methods=["GET"])
def get_single_conversation(conversation_id):
    conv = get_conversation(conversation_id)
    if not conv:
        return jsonify({
            "error": "Conversation not found."
        }), 404

    return jsonify({
        "id": conv["id"],
        "title": conv.get("title", "New Conversation"),
        "created_at": conv.get("created_at"),
        "updated_at": conv.get("updated_at"),
        "messages": conv.get("messages", [])
    }), 200
