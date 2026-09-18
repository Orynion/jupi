import os
import random

# Reconfigure stdout/stderr to UTF-8 before anything else (including the
# google-genai library) gets a chance to print. The brain module is imported
# by `main.py` and by `app/core/web.py`, both of which expect to print
# Saturnia's emoji-laden responses without crashing on Windows consoles
# (PowerShell, cmd) that default to cp1252 / IBM437.
import app.core.console  # noqa: F401  (side effect: reconfigure streams)

from dotenv import load_dotenv
from google import genai

from app.core.memory import (
    add_conversation_message,
    get_conversation,
    get_conversation_history,
    remember,
    recall,
    save_message,
)
from app.core.personality import SATURNIA_PERSONALITY
from app.core.quirks import maybe_quirk
from app.core.router import route

from app.core.math_engine import solve
from app.core.algebra_engine import solve as solve_algebra
from app.core.quadratic_engine import solve as solve_quadratic
from app.core.fraction_algebra_engine import solve as solve_fraction_algebra
from app.core.system_algebra_engine import solve as solve_system
from app.core.power_root_engine import solve as solve_power_root


# ============================================================
# GEMINI SETUP
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError(
        "GEMINI_API_KEY was not found in .env"
    )

client = genai.Client(api_key=api_key)


# ============================================================
# SHORT-TERM CONVERSATION MEMORY
# ============================================================

# The in-memory conversation context holds at most this many individual
# messages (user and assistant entries are counted separately, matching
# the existing representation). Once the limit is reached, the oldest
# entries are dropped from memory. The persisted history written by the
# memory system (saturnia_memory.json) keeps its own records and is not
# affected by this in-context limit.

MAX_HISTORY_MESSAGES = 100

conversation_history = []


def load_conversation_history():

    # Restore the conversation history that a previous Saturnia process
    # persisted via the memory system. Entries are normalized to the same
    # shape that save_conversation() produces (role + text).

    conversation_history.clear()

    for item in get_conversation_history(limit=100):

        conversation_history.append({
            "role": item["role"],
            "text": item["text"],
        })


def save_conversation(user_text, assistant_text, conversation_id=None):

    if conversation_id:
        add_conversation_message(conversation_id, "user", user_text)
        add_conversation_message(conversation_id, "assistant", assistant_text)
        return

    conversation_history.append({
        "role": "user",
        "text": user_text
    })

    conversation_history.append({
        "role": "assistant",
        "text": assistant_text
    })

    # Enforce the in-memory context limit: keep only the newest
    # MAX_HISTORY_MESSAGES entries and discard older ones. In-place
    # slice assignment preserves the list object itself, so any other
    # references to conversation_history stay valid. Persistence (the
    # save_message calls below) is unaffected by this cap.

    if len(conversation_history) > MAX_HISTORY_MESSAGES:

        conversation_history[:] = (
            conversation_history[-MAX_HISTORY_MESSAGES:]
        )

    # Persist both messages through the existing memory system so the
    # conversation survives a process restart. Each message is written to
    # disk exactly once: the in-memory history above is never re-read from
    # disk during the session, so no duplicate entries are created.

    save_message("user", user_text)
    save_message("assistant", assistant_text)


# Load any conversation history persisted by a previous session.
load_conversation_history()


# ============================================================
# SATURNIA GREETINGS
# ============================================================

GREETINGS = [
    "Hello 👋 I am waking up.",
    "Ello 👋",
    "Hello!",
    "Hola! 👋",
    "Namaste 🙏",
    "Well hello!",
    "Hello there!",
    "Hi mate!",
    "Hey there!",
    "Hello mate!",
    "Welcome back. 🪐",
]


def get_greeting():
    return random.choice(GREETINGS)


# ============================================================
# MAIN BRAIN
# ============================================================

def think(message, conversation_id=None):

    original_message = message
    message_lower = message.lower().strip()

    # ========================================================
    # ROUTER
    # ========================================================

    destination = route(original_message)

    coding_instruction = ""

    if destination == "coding":

        coding_instruction = """

CODING REQUEST
--------------

Answer the user's programming question directly. Include practical code when
appropriate, explain the relevant fix briefly, and do not claim to have run
the code unless the user provided the result.
"""

    # ========================================================
    # GREETING
    # ========================================================

    if destination == "greeting":

        answer = get_greeting()

        if conversation_id:
            save_conversation(
                original_message,
                answer,
                conversation_id
            )
        else:
            save_conversation(
                original_message,
                answer
            )

        return answer

    # ========================================================
    # MEMORY
    # ========================================================

    if destination == "memory":

        if "my name is" in message_lower:

            phrase = "my name is"
            start = original_message.lower().find(phrase)

            if start >= 0:
                name = original_message[
                    start + len(phrase):
                ].strip().rstrip(".,!?;:")
            else:
                name = ""

            name = name.strip()

            remember(
                "name",
                name
            )

            answer = f"Nice to meet you, {name}."

        else:

            name = recall("name")

            if name:
                answer = f"Your name is {name}."
            else:
                answer = "I don't know your name yet."

        if conversation_id:
            save_conversation(
                original_message,
                answer,
                conversation_id
            )
        else:
            save_conversation(
                original_message,
                answer
            )

        return answer

    # ========================================================
    # MATH ENGINES
    # ========================================================
    #
    # Math stays local.
    # We do NOT send basic math to Gemini.
    #

    solvers = (
        solve_system,
        solve_power_root,
        solve_quadratic,
        solve_fraction_algebra,
        solve_algebra,
        solve,
    )

    for solver in solvers:

        result = solver(
            original_message
        )

        if result is None:
            continue

        answer = str(
            result["answer"]
        )

        if conversation_id:
            save_conversation(
                original_message,
                answer,
                conversation_id
            )
        else:
            save_conversation(
                original_message,
                answer
            )

        return answer

    # ========================================================
    # GEMINI CONVERSATION
    # ========================================================

    conversation_text = (
        SATURNIA_PERSONALITY
        + coding_instruction
        + """

CONVERSATION HISTORY
--------------------

"""
    )

    if conversation_id:
        conv = get_conversation(conversation_id)
        if conv and "messages" in conv:
            active_history = [
                {
                    "role": m.get("role", "user"),
                    "text": m.get("content", m.get("text", "")),
                }
                for m in conv["messages"]
            ]
            if len(active_history) > MAX_HISTORY_MESSAGES:
                active_history = active_history[-MAX_HISTORY_MESSAGES:]
        else:
            active_history = []
    else:
        active_history = conversation_history

    for item in active_history:

        if item["role"] == "user":

            conversation_text += (
                f"\nUser: {item['text']}"
            )

        else:

            conversation_text += (
                f"\nAssistant: {item['text']}"
            )

    conversation_text += (
        f"\nUser: {original_message}"
    )

    conversation_text += "\nAssistant:"

    try:

        response = client.models.generate_content(
            model="gemini-3.1-flash-lite",
            contents=conversation_text
        )

        answer = response.text.strip()

        # Remove accidental prefixes.

        if answer.startswith("Saturnia:"):

            answer = answer[
                len("Saturnia:"):
            ].strip()

        if answer.startswith("Assistant:"):

            answer = answer[
                len("Assistant:"):
            ].strip()

        # ====================================================
        # CONTEXT-AWARE QUIRK
        # ====================================================

        quirk = maybe_quirk(
            original_message
        )

        if quirk:

            answer = (
                f"{answer}\n\n{quirk}"
            )

        if conversation_id:
            save_conversation(
                original_message,
                answer,
                conversation_id
            )
        else:
            save_conversation(
                original_message,
                answer
            )

        return answer

    except Exception as e:

        return (
            "I ran into a problem talking "
            f"to Gemini: {e}"
        )


# ============================================================
# FOLLOW-UP QUESTIONS
# ============================================================

def ask_for_more(topic):

    questions = {

        "problem":
            "Can you tell me more about what's happening?",

        "coding":
            "What error are you seeing?",

        "unknown":
            "What makes you think that?"
    }

    return questions.get(
        topic,
        "Can you tell me more?"
    )