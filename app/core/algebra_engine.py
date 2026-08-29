import re


# ============================================================
# ALGEBRA ENGINE V1.1
# ============================================================
#
# Solves linear equations containing:
#
# x + 7 = 19
# 3x = 21
# 2x + 5 = 17
# 2x + 5 = 3x - 1
#
# AND parentheses:
#
# 2(x + 3) = 14
# 3(x - 2) + 4 = 16
# 2(x + 5) = x + 17
#
# Pipeline:
#
# Equation
#    ↓
# Expand parentheses
#    ↓
# Collect x terms
#    ↓
# Collect constants
#    ↓
# Solve
#    ↓
# Verify
# ============================================================


def clean(text):
    text = text.lower().strip()

    text = text.replace(" ", "")
    text = text.replace("−", "-")
    text = text.replace("–", "-")

    return text


# ------------------------------------------------------------
# EXPAND PARENTHESES
# ------------------------------------------------------------

def expand_parentheses(expression):
    """
    Expand simple linear parentheses.

    Examples:

        2(x+3) → 2x+6
        3(x-2) → 3x-6
        -2(x+4) → -2x-8
    """

    pattern = r"(-?\d+(?:\.\d+)?)\((x|x[+-]\d+(?:\.\d+)?)\)"

    while "(" in expression:

        match = re.search(pattern, expression)

        if not match:
            return None

        multiplier = float(match.group(1))
        inside = match.group(2)

        if inside == "x":
            expanded = f"{multiplier}x"

        elif "+" in inside:
            x_part, number_part = inside.split("+")
            number = float(number_part)

            expanded = (
                f"{multiplier}x"
                f"+{multiplier * number}"
            )

        elif "-" in inside:

            x_part, number_part = inside.split("-", 1)
            number = float(number_part)

            expanded = (
                f"{multiplier}x"
                f"-{multiplier * number}"
            )

        else:
            return None

        expression = (
            expression[:match.start()]
            + expanded
            + expression[match.end():]
        )

    return expression


# ------------------------------------------------------------
# PARSE LINEAR EXPRESSION
# ------------------------------------------------------------

def parse_linear_side(side):
    """
    Converts:

        2x+5

    into:

        coefficient = 2
        constant = 5
    """

    side = side.replace("-", "+-")

    terms = side.split("+")

    coefficient = 0
    constant = 0

    for term in terms:

        if not term:
            continue

        # x
        if term == "x":
            coefficient += 1
            continue

        # -x
        if term == "-x":
            coefficient -= 1
            continue

        # coefficient x
        match = re.fullmatch(
            r"(-?\d+(?:\.\d+)?)x",
            term
        )

        if match:

            coefficient += float(
                match.group(1)
            )

            continue

        # constant
        match = re.fullmatch(
            r"-?\d+(?:\.\d+)?",
            term
        )

        if match:

            constant += float(term)

            continue

        raise ValueError(
            f"Unsupported term: {term}"
        )

    return coefficient, constant


# ------------------------------------------------------------
# EVALUATE EXPRESSION
# ------------------------------------------------------------

def evaluate_side(side, x):

    side = side.replace("-", "+-")

    terms = side.split("+")

    total = 0

    for term in terms:

        if not term:
            continue

        if term == "x":
            total += x
            continue

        if term == "-x":
            total -= x
            continue

        match = re.fullmatch(
            r"(-?\d+(?:\.\d+)?)x",
            term
        )

        if match:

            coefficient = float(
                match.group(1)
            )

            total += coefficient * x

            continue

        match = re.fullmatch(
            r"-?\d+(?:\.\d+)?",
            term
        )

        if match:

            total += float(term)

            continue

        raise ValueError(
            f"Cannot evaluate: {term}"
        )

    return total


# ------------------------------------------------------------
# VERIFY
# ------------------------------------------------------------

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

        return abs(
            left_value - right_value
        ) < 1e-9

    except Exception:
        return False


# ------------------------------------------------------------
# SOLVE
# ------------------------------------------------------------

def solve_linear(equation):

    try:

        left, right = equation.split("=")

        # Expand parentheses on both sides.
        left_expanded = expand_parentheses(left)
        right_expanded = expand_parentheses(right)

        if left_expanded is None:
            return None

        if right_expanded is None:
            return None

        left_x, left_constant = (
            parse_linear_side(left_expanded)
        )

        right_x, right_constant = (
            parse_linear_side(right_expanded)
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

        # No x remains.
        if coefficient == 0:

            if constant == 0:

                return {
                    "type": "algebra",
                    "answer": "infinitely many solutions",
                    "verified": True,
                    "steps": [
                        "Expand both sides.",
                        "The x terms cancel.",
                        "Both sides are equivalent.",
                        "Every value of x works."
                    ]
                }

            return {
                "type": "algebra",
                "answer": "no solution",
                "verified": True,
                "steps": [
                    "Expand both sides.",
                    "The x terms cancel.",
                    "The remaining statement is false.",
                    "Therefore there is no solution."
                ]
            }

        x = constant / coefficient

        # Clean integer results.
        if abs(x - round(x)) < 1e-10:
            x = int(round(x))

        # Verify against the expanded equation.
        verified = verify(
            f"{left_expanded}={right_expanded}",
            x
        )

        if not verified:
            return None

        return {
            "type": "algebra",
            "answer": x,
            "verified": True,
            "steps": [
                f"Original equation: {equation}",
                f"Expanded equation: "
                f"{left_expanded} = {right_expanded}",
                "Collect the x terms.",
                "Collect the constants.",
                f"Solve for x: x = {x}",
                f"Verification passed: x = {x}"
            ]
        }

    except Exception:
        return None


# ------------------------------------------------------------
# DETECTION
# ------------------------------------------------------------

def looks_like_algebra(text):

    text = clean(text)

    return (
        "=" in text
        and "x" in text
    )


# ------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------

def solve(question):
    # Extract the equation part and remove prefixes like "solve", "solve for", etc.
    if "=" not in question:
        return None
    
    # Split on the equals sign
    parts = question.split("=")
    if len(parts) != 2:
        return None
    
    # Remove common prefixes from the left side
    left = parts[0].strip()
    left = re.sub(r'^(solve\s+for\s+|solve\s+|find\s+)', '', left, flags=re.IGNORECASE)
    
    right = parts[1].strip()
    
    # Reconstruct the equation
    equation = f"{left}={right}"
    equation = clean(equation)

    if not looks_like_algebra(equation):
        return None

    return solve_linear(equation)
