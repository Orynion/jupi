import re
from fractions import Fraction


# ============================================================
# SYSTEM ALGEBRA ENGINE V1
# ============================================================
#
# Solves systems such as:
#
# x + y = 10
# x - y = 2
#
# and:
#
# 2x + 3y = 13
# x - y = 1
#
# Uses elimination with exact fractions.
# ============================================================


def clean(text):
    text = text.lower().strip()

    text = text.replace(" ", "")
    text = text.replace("−", "-")
    text = text.replace("–", "-")

    return text


# ------------------------------------------------------------
# DETECTION
# ------------------------------------------------------------

def looks_like_system(text):

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    return (
        len(lines) == 2
        and "=" in lines[0]
        and "=" in lines[1]
        and "x" in text.lower()
        and "y" in text.lower()
    )


# ------------------------------------------------------------
# PARSE ONE EQUATION
# ------------------------------------------------------------

def parse_equation(equation):

    equation = clean(equation)

    left, right = equation.split("=")

    left_x, left_y, left_constant = parse_side(left)
    right_x, right_y, right_constant = parse_side(right)

    # Move everything to the left:
    #
    # ax + by = c

    a = left_x - right_x
    b = left_y - right_y
    c = right_constant - left_constant

    return a, b, c


# ------------------------------------------------------------
# PARSE SIDE
# ------------------------------------------------------------

def parse_side(side):

    side = side.replace("-", "+-")

    terms = side.split("+")

    x_coefficient = Fraction(0)
    y_coefficient = Fraction(0)
    constant = Fraction(0)

    for term in terms:

        if not term:
            continue

        # ----------------------------------------------------
        # x
        # ----------------------------------------------------

        if term == "x":
            x_coefficient += 1
            continue

        if term == "-x":
            x_coefficient -= 1
            continue

        # ----------------------------------------------------
        # y
        # ----------------------------------------------------

        if term == "y":
            y_coefficient += 1
            continue

        if term == "-y":
            y_coefficient -= 1
            continue

        # ----------------------------------------------------
        # ax
        # ----------------------------------------------------

        match = re.fullmatch(
            r"(-?\d+)x",
            term
        )

        if match:

            x_coefficient += Fraction(
                int(match.group(1))
            )

            continue

        # ----------------------------------------------------
        # by
        # ----------------------------------------------------

        match = re.fullmatch(
            r"(-?\d+)y",
            term
        )

        if match:

            y_coefficient += Fraction(
                int(match.group(1))
            )

            continue

        # ----------------------------------------------------
        # CONSTANT
        # ----------------------------------------------------

        match = re.fullmatch(
            r"-?\d+",
            term
        )

        if match:

            constant += Fraction(
                int(term)
            )

            continue

        raise ValueError(
            f"Unsupported term: {term}"
        )

    return (
        x_coefficient,
        y_coefficient,
        constant
    )


# ------------------------------------------------------------
# FORMAT
# ------------------------------------------------------------

def format_fraction(value):

    if value.denominator == 1:
        return str(value.numerator)

    return (
        f"{value.numerator}"
        f"/"
        f"{value.denominator}"
    )


# ------------------------------------------------------------
# VERIFY
# ------------------------------------------------------------

def verify(a, b, c, x, y):

    return (
        a * x + b * y == c
    )


# ------------------------------------------------------------
# SOLVE
# ------------------------------------------------------------

def solve_system(equation1, equation2):

    try:

        a1, b1, c1 = parse_equation(
            equation1
        )

        a2, b2, c2 = parse_equation(
            equation2
        )

        # ----------------------------------------------------
        # DETERMINANT
        # ----------------------------------------------------

        determinant = (
            a1 * b2
            - a2 * b1
        )

        # Parallel / dependent equations.
        if determinant == 0:

            return {
                "type": "system",
                "answer": "No unique solution",
                "verified": False
            }

        # ----------------------------------------------------
        # CRAMER'S RULE
        # ----------------------------------------------------
        #
        # x = (c1*b2 - c2*b1) / determinant
        #
        # y = (a1*c2 - a2*c1) / determinant
        # ----------------------------------------------------

        x = (
            c1 * b2
            - c2 * b1
        ) / determinant

        y = (
            a1 * c2
            - a2 * c1
        ) / determinant

        # ----------------------------------------------------
        # VERIFY
        # ----------------------------------------------------

        verified = (
            verify(a1, b1, c1, x, y)
            and verify(a2, b2, c2, x, y)
        )

        if not verified:
            return None

        x_text = format_fraction(x)
        y_text = format_fraction(y)

        return {
            "type": "system",
            "answer": (
                f"x = {x_text}, "
                f"y = {y_text}"
            ),
            "x": x,
            "y": y,
            "verified": True,
            "steps": [
                "Parse both equations.",
                "Move variables to the left.",
                "Use elimination / Cramer's rule.",
                f"x = {x_text}",
                f"y = {y_text}",
                "Verification passed."
            ]
        }

    except Exception:
        return None


# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------

def solve(question):

    lines = [
        line.strip()
        for line in question.splitlines()
        if line.strip()
    ]

    if not looks_like_system(question):
        return None

    return solve_system(
        lines[0],
        lines[1]
    )
