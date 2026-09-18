import os

from flask import Flask, request
from flask_cors import CORS
from markupsafe import escape

# Ensure stdout/stderr are reconfigured to UTF-8 before anything else prints.
# This prevents `UnicodeEncodeError` when Werkzeug prints startup info or
# tracebacks on terminals that default to cp1252 / IBM437 (e.g. PowerShell).
import app.core.console  # noqa: F401
from app.core.api_v1 import api_v1
from app.core.brain import think


def get_allowed_origins():
    custom_origins = os.getenv("SATURNIA_ALLOWED_ORIGINS", "").strip()
    if custom_origins:
        return [
            origin.strip()
            for origin in custom_origins.split(",")
            if origin.strip()
        ]
    return [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]


app = Flask(__name__)
app.register_blueprint(api_v1)

CORS(
    app,
    resources={r"/api/*": {"origins": get_allowed_origins()}},
    methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True,
)


def flask_debug_enabled():
    value = os.getenv("FLASK_DEBUG", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


# ============================================================
# CHAT HISTORY
# ============================================================

chat_history = []


# ============================================================
# WEB CHAT PAGE
# ============================================================

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        message = request.form.get(
            "message",
            ""
        ).strip()

        if message:

            response = think(message)

            chat_history.append({
                "user": message,
                "ai": response
            })

    return f"""
<!DOCTYPE html>

<html>

<head>

    <title>AI or is it?</title>

    <style>

        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
        }}

        h1 {{
            text-align: center;
        }}

        .chat {{
            background: white;
            padding: 20px;
            border-radius: 12px;
            min-height: 300px;
            margin-bottom: 20px;
        }}

        .message {{
            margin-bottom: 20px;
        }}

        .user {{
            font-weight: bold;
        }}

        .ai {{
            margin-top: 6px;
            white-space: pre-wrap;
        }}

        form {{
            display: flex;
            gap: 10px;
        }}

        input {{
            flex: 1;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ccc;
            border-radius: 8px;
        }}

        button {{
            padding: 12px 20px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }}

    </style>

</head>


<body>

    <h1>AI or is it? 🤖</h1>


    <div class="chat">

        {
            "".join(
                f'''
                <div class="message">

                    <div class="user">
                        You: {escape(chat["user"])}
                    </div>

                    <div class="ai">
                        AI: {escape(chat["ai"])}
                    </div>

                </div>
                '''
                for chat in chat_history
            )
        }

    </div>


    <form method="post">

        <input
            name="message"
            placeholder="Talk to me..."
            autocomplete="off"
            autofocus
        >

        <button type="submit">
            Send
        </button>

    </form>


</body>

</html>
"""


# ============================================================
# API FOR LOVABLE / OTHER FRONTENDS
# ============================================================

@app.route("/api/chat", methods=["POST"])
def api_chat():

    data = request.get_json(silent=True)

    if not data or not isinstance(data, dict):

        return {
            "error": "No JSON data received."
        }, 400

    raw_message = data.get(
        "message",
        ""
    )
    if not isinstance(raw_message, str):
        return {
            "error": "Message cannot be empty."
        }, 400

    message = raw_message.strip()

    if not message:

        return {
            "error": "Message cannot be empty."
        }, 400

    response = think(message)

    return {
        "response": response
    }


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=flask_debug_enabled()
    )
