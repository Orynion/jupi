import re
from fractions import Fraction


# ============================================================
# FRACTION ALGEBRA ENGINE V1
# ============================================================
#
# Handles linear equations containing fractions:
#
# x/3 + 2 = 7
# x/4 = 5
# 2x/3 = 10
# x/2 + x/3 = 10
#
# Converts every side into:
#
#     coefficient * x + constant
#
# using exact fractions instead of floating-point numbers.
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

def looks_like_fraction_algebra(text):

    text = clean(text)

    return (
        "=" in text
        and "x" in text
        and "/" in text
    )


# ------------------------------------------------------------
# PARSE A NUMBER
# ------------------------------------------------------------

def parse_number(text):

    if "/" in text:

        numerator, denominator = text.split("/")

        denominator = int(denominator)

        if denominator == 0:
            raise ValueError("Division by zero")

        return Fraction(
            int(numerator),
            denominator
        )

    return Fraction(text)


# ------------------------------------------------------------
# PARSE LINEAR SIDE
# ------------------------------------------------------------

def parse_side(side):
    """
    Converts a linear expression into:

        coefficient_of_x
        constant

    Examples:

        x/3       -> (1/3, 0)
        2x/3      -> (2/3, 0)
        x/2 + 4   -> (1/2, 4)
        2x/3 - 5  -> (2/3, -5)
    """

    # Turn subtraction into addition of negatives.
    side = side.replace("-", "+-")

    terms = side.split("+")

    coefficient = Fraction(0)
    constant = Fraction(0)

    for term in terms:

        if not term:
            continue

        # ----------------------------------------------------
        # x/n
        # ----------------------------------------------------

        match = re.fullmatch(
            r"x/(\d+)",
            term
        )

        if match:

            denominator = int(match.group(1))

            if denominator == 0:
                raise ValueError("Division by zero")

            coefficient += Fraction(
                1,
                denominator
            )

            continue

        # ----------------------------------------------------
        # -x/n
        # ----------------------------------------------------

        match = re.fullmatch(
            r"-x/(\d+)",
            term
        )

        if match:

            denominator = int(match.group(1))

            if denominator == 0:
                raise ValueError("Division by zero")

            coefficient -= Fraction(
                1,
                denominator
            )

            continue

        # ----------------------------------------------------
        # ax/n
        # ----------------------------------------------------

        match = re.fullmatch(
            r"(-?\d+)x/(\d+)",
            term
        )

        if match:

            numerator = int(match.group(1))
            denominator = int(match.group(2))

            if denominator == 0:
                raise ValueError("Division by zero")

            coefficient += Fraction(
                numerator,
                denominator
            )

            continue

        # ----------------------------------------------------
        # x
        # ----------------------------------------------------

        if term == "x":

            coefficient += Fraction(1)

            continue

        # ----------------------------------------------------
        # -x
        # ----------------------------------------------------

        if term == "-x":

            coefficient -= Fraction(1)

            continue

        # ----------------------------------------------------
        # CONSTANT
        # ----------------------------------------------------

        if re.fullmatch(
            r"-?\d+(?:/\d+)?",
            term
        ):

            constant += parse_number(term)

            continue

        raise ValueError(
            f"Unsupported term: {term}"
        )

    return coefficient, constant


# ------------------------------------------------------------
# FORMAT FRACTIONS
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

def evaluate_side(side, x):

    coefficient, constant = parse_side(side)

    return (
        coefficient * x
        + constant
    )


def verify(equation, x):

    try:

        left, right = equation.split("=")

        left_value = evaluate_side(
            left,
            x
        )

        right_value = evaluate_side(
            right,
            x
        )

        return left_value == right_value

    except Exception:
        return False


# ------------------------------------------------------------
# SOLVE
# ------------------------------------------------------------

def solve_linear(equation):

    try:

        left, right = equation.split("=")

        left_x, left_constant = (
            parse_side(left)
        )

        right_x, right_constant = (
            parse_side(right)
        )

        # ax + b = cx + d
        #
        # ax - cx = d - b
        #
        # x = (d - b) / (a - c)

        coefficient = (
            left_x - right_x
        )

        constant = (
            right_constant
            - left_constant
        )

        # ----------------------------------------------------
        # No x coefficient
        # ----------------------------------------------------

        if coefficient == 0:

            if constant == 0:

                return {
                    "type": "fraction_algebra",
                    "answer": "infinitely many solutions",
                    "verified": True
                }

            return {
                "type": "fraction_algebra",
                "answer": "no solution",
                "verified": True
            }

        x = constant / coefficient

        if not verify(equation, x):
            return None

        answer = format_fraction(x)

        return {
            "type": "fraction_algebra",
            "answer": f"x = {answer}",
            "value": x,
            "verified": True,
            "steps": [
                f"Collect the x terms.",
                f"Collect the constants.",
                f"x = {answer}",
                "Substitute the result back into the equation.",
                "Verification passed."
            ]
        }

    except Exception:
        return None


# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------

def solve(question):

    equation = clean(question)

    if not looks_like_fraction_algebra(equation):
        return None

    return solve_linear(equation)
