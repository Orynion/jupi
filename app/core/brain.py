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

from app.core.memory import remember, recall
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

conversation_history = []


def save_conversation(user_text, assistant_text):

    conversation_history.append({
        "role": "user",
        "text": user_text
    })

    conversation_history.append({
        "role": "assistant",
        "text": assistant_text
    })


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

def think(message):

    original_message = message
    message_lower = message.lower().strip()

    # ========================================================
    # ROUTER
    # ========================================================

    destination = route(original_message)

    # ========================================================
    # GREETING
    # ========================================================

    if destination == "greeting":

        answer = get_greeting()

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

            name = message_lower.replace(
                "my name is",
                ""
            ).strip()

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

    system_result = solve_system(
        original_message
    )

    if system_result:

        answer = str(
            system_result["answer"]
        )

        save_conversation(
            original_message,
            answer
        )

        return answer

    power_root_result = solve_power_root(
        original_message
    )

    if power_root_result:

        answer = str(
            power_root_result["answer"]
        )

        save_conversation(
            original_message,
            answer
        )

        return answer

    quadratic_result = solve_quadratic(
        original_message
    )

    if quadratic_result:

        answer = str(
            quadratic_result["answer"]
        )

        save_conversation(
            original_message,
            answer
        )

        return answer

    fraction_result = solve_fraction_algebra(
        original_message
    )

    if fraction_result:

        answer = str(
            fraction_result["answer"]
        )

        save_conversation(
            original_message,
            answer
        )

        return answer

    algebra_result = solve_algebra(
        original_message
    )

    if algebra_result:

        answer = str(
            algebra_result["answer"]
        )

        save_conversation(
            original_message,
            answer
        )

        return answer

    math_result = solve(
        original_message
    )

    if math_result:

        answer = str(
            math_result["answer"]
        )

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
        + """

CONVERSATION HISTORY
--------------------

"""
    )

    for item in conversation_history:

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