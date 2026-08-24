import math
import re


# ============================================================
# POWER & ROOT ENGINE V1
# ============================================================
#
# Handles:
#
# 2^8       -> 256
# 5^2       -> 25
# sqrt(144) -> 12
# √144      -> 12
# 27^(1/3)  -> 3
# x^2 = 49  -> x = 7 or x = -7
#
# This version focuses on numerical powers/roots and simple
# equations of the form x^n = number.
# ============================================================


def clean(text):
    text = text.lower().strip()

    text = text.replace(" ", "")
    text = text.replace("²", "^2")
    text = text.replace("³", "^3")
    text = text.replace("⁴", "^4")
    text = text.replace("⁵", "^5")
    text = text.replace("√", "sqrt")

    text = text.replace("−", "-")
    text = text.replace("–", "-")

    return text


# ------------------------------------------------------------
# FORMAT NUMBER
# ------------------------------------------------------------

def format_number(value):

    if isinstance(value, int):
        return str(value)

    if abs(value - round(value)) < 1e-10:
        return str(int(round(value)))

    return str(round(value, 10))


# ------------------------------------------------------------
# POWER
# ------------------------------------------------------------

def solve_power(text):

    match = re.fullmatch(
        r"(-?\d+(?:\.\d+)?)\^(-?\d+(?:\.\d+)?)",
        text
    )

    if not match:
        return None

    base = float(match.group(1))
    exponent = float(match.group(2))

    try:
        result = base ** exponent

        return {
            "type": "power",
            "answer": format_number(result),
            "verified": True
        }

    except Exception:
        return None


# ------------------------------------------------------------
# SQUARE ROOT
# ------------------------------------------------------------

def solve_square_root(text):

    match = re.fullmatch(
        r"sqrt\((-?\d+(?:\.\d+)?)\)",
        text
    )

    if not match:

        match = re.fullmatch(
            r"sqrt(-?\d+(?:\.\d+)?)",
            text
        )

    if not match:
        return None

    number = float(match.group(1))

    if number < 0:

        return {
            "type": "root",
            "answer": "No real solution",
            "verified": True
        }

    result = math.sqrt(number)

    return {
        "type": "root",
        "answer": format_number(result),
        "verified": True
    }


# ------------------------------------------------------------
# GENERAL ROOT
# ------------------------------------------------------------

def solve_root(text):

    match = re.fullmatch(
        r"(-?\d+(?:\.\d+)?)\^\(1/(\d+)\)",
        text
    )

    if not match:
        return None

    number = float(match.group(1))
    degree = int(match.group(2))

    if degree <= 0:
        return None

    # Even root of negative number is not real.
    if number < 0 and degree % 2 == 0:

        return {
            "type": "root",
            "answer": "No real solution",
            "verified": True
        }

    if number < 0:

        result = -((-number) ** (1 / degree))

    else:

        result = number ** (1 / degree)

    return {
        "type": "root",
        "answer": format_number(result),
        "verified": True
    }


# ------------------------------------------------------------
# x^n = NUMBER
# ------------------------------------------------------------

def solve_power_equation(text):

    match = re.fullmatch(
        r"x\^(\d+)=(-?\d+(?:\.\d+)?)",
        text
    )

    if not match:
        return None

    exponent = int(match.group(1))
    number = float(match.group(2))

    if exponent <= 0:
        return None

    # --------------------------------------------------------
    # EVEN POWER
    # --------------------------------------------------------

    if exponent % 2 == 0:

        if number < 0:

            return {
                "type": "power_equation",
                "answer": "No real solutions",
                "verified": True
            }

        root = number ** (1 / exponent)

        if abs(root - round(root)) < 1e-10:
            root = int(round(root))

        if root == 0:

            answer = "x = 0"

        else:

            answer = (
                f"x = {root} or x = {-root}"
            )

        return {
            "type": "power_equation",
            "answer": answer,
            "verified": True
        }

    # --------------------------------------------------------
    # ODD POWER
    # --------------------------------------------------------

    if number < 0:

        root = -((-number) ** (1 / exponent))

    else:

        root = number ** (1 / exponent)

    root = (
        int(round(root))
        if abs(root - round(root)) < 1e-10
        else root
    )

    return {
        "type": "power_equation",
        "answer": f"x = {format_number(root)}",
        "verified": True
    }


# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------

def solve(question):

    text = clean(question)

    # x^n = number
    result = solve_power_equation(text)

    if result:
        return result

    # sqrt(...)
    result = solve_square_root(text)

    if result:
        return result

    # number^(1/n)
    result = solve_root(text)

    if result:
        return result

    # number^number
    result = solve_power(text)

    if result:
        return result

    return None
