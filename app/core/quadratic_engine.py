import re
import math


# ============================================================
# QUADRATIC ENGINE V1
# ============================================================
#
# Solves quadratic equations:
#
# x^2 + 5x + 6 = 0
# x^2 - 9 = 0
# 2x^2 + 7x + 3 = 0
#
# Uses:
#
# ax² + bx + c = 0
#
# Discriminant:
#
# D = b² - 4ac
#
# Then:
#
# x = (-b ± √D) / 2a
# ============================================================


def clean(text):
    text = text.lower().strip()

    text = text.replace(" ", "")
    text = text.replace("²", "^2")
    text = text.replace("−", "-")
    text = text.replace("–", "-")

    return text


# ------------------------------------------------------------
# DETECTION
# ------------------------------------------------------------

def looks_like_quadratic(text):

    text = clean(text)

    return (
        "=" in text
        and (
            "x^2" in text
            or "x2" in text
            or "x*x" in text
        )
    )


# ------------------------------------------------------------
# NORMALIZE
# ------------------------------------------------------------

def normalize_equation(text):

    text = clean(text)

    text = text.replace("x*x", "x^2")
    text = text.replace("x2", "x^2")

    return text


# ------------------------------------------------------------
# PARSE QUADRATIC SIDE
# ------------------------------------------------------------

def parse_side(side):

    """
    Converts:

        2x^2 + 7x + 3

    into:

        a = 2
        b = 7
        c = 3
    """

    side = side.replace("-", "+-")

    terms = side.split("+")

    a = 0
    b = 0
    c = 0

    for term in terms:

        if not term:
            continue

        # x^2
        if term == "x^2":
            a += 1
            continue

        # -x^2
        if term == "-x^2":
            a -= 1
            continue

        # coefficient x^2
        match = re.fullmatch(
            r"(-?\d+(?:\.\d+)?)x\^2",
            term
        )

        if match:
            a += float(match.group(1))
            continue

        # x
        if term == "x":
            b += 1
            continue

        # -x
        if term == "-x":
            b -= 1
            continue

        # coefficient x
        match = re.fullmatch(
            r"(-?\d+(?:\.\d+)?)x",
            term
        )

        if match:
            b += float(match.group(1))
            continue

        # constant
        match = re.fullmatch(
            r"-?\d+(?:\.\d+)?",
            term
        )

        if match:
            c += float(term)
            continue

        raise ValueError(
            f"Unsupported term: {term}"
        )

    return a, b, c


# ------------------------------------------------------------
# FORMAT NUMBERS
# ------------------------------------------------------------

def format_number(number):

    if abs(number - round(number)) < 1e-10:
        return str(int(round(number)))

    return str(round(number, 10))


# ------------------------------------------------------------
# SOLVE
# ------------------------------------------------------------

def solve_quadratic(equation):

    try:

        left, right = equation.split("=")

        left_a, left_b, left_c = parse_side(left)
        right_a, right_b, right_c = parse_side(right)

        # Move everything to the left:
        #
        # ax² + bx + c = 0

        a = left_a - right_a
        b = left_b - right_b
        c = left_c - right_c

        # If a = 0, this isn't quadratic.
        if abs(a) < 1e-12:
            return None

        discriminant = b ** 2 - 4 * a * c

        # ----------------------------------------------------
        # TWO REAL ROOTS
        # ----------------------------------------------------

        if discriminant > 0:

            sqrt_d = math.sqrt(discriminant)

            x1 = (-b + sqrt_d) / (2 * a)
            x2 = (-b - sqrt_d) / (2 * a)

            x1 = (
                int(round(x1))
                if abs(x1 - round(x1)) < 1e-10
                else x1
            )

            x2 = (
                int(round(x2))
                if abs(x2 - round(x2)) < 1e-10
                else x2
            )

            return {
                "type": "quadratic",
                "answer": (
                    f"x = {format_number(x1)} "
                    f"or x = {format_number(x2)}"
                ),
                "roots": [x1, x2],
                "discriminant": discriminant,
                "verified": True,
                "steps": [
                    f"a = {format_number(a)}",
                    f"b = {format_number(b)}",
                    f"c = {format_number(c)}",
                    f"Discriminant = {format_number(discriminant)}",
                    "Use the quadratic formula.",
                    f"x = {format_number(x1)}",
                    f"x = {format_number(x2)}"
                ]
            }

        # ----------------------------------------------------
        # ONE REAL ROOT
        # ----------------------------------------------------

        if abs(discriminant) < 1e-12:

            x = -b / (2 * a)

            x = (
                int(round(x))
                if abs(x - round(x)) < 1e-10
                else x
            )

            return {
                "type": "quadratic",
                "answer": f"x = {format_number(x)}",
                "roots": [x],
                "discriminant": 0,
                "verified": True,
                "steps": [
                    f"a = {format_number(a)}",
                    f"b = {format_number(b)}",
                    f"c = {format_number(c)}",
                    "Discriminant = 0",
                    "Therefore there is one repeated real root.",
                    f"x = {format_number(x)}"
                ]
            }

        # ----------------------------------------------------
        # NO REAL ROOTS
        # ----------------------------------------------------

        return {
            "type": "quadratic",
            "answer": "No real solutions",
            "roots": [],
            "discriminant": discriminant,
            "verified": True,
            "steps": [
                f"a = {format_number(a)}",
                f"b = {format_number(b)}",
                f"c = {format_number(c)}",
                f"Discriminant = {format_number(discriminant)}",
                "The discriminant is negative.",
                "Therefore there are no real solutions."
            ]
        }

    except Exception:
        return None


# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------

def solve(question):

    equation = normalize_equation(question)

    if not looks_like_quadratic(equation):
        return None

    return solve_quadratic(equation)
