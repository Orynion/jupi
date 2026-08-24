import ast
import math
import operator
import re


# ============================================================
# MATH ENGINE V1.1
# ============================================================
#
# Understand → Plan → Calculate → Verify → Answer
#
# This version supports:
# - Arithmetic
# - Percentages
# - Fractions
# - Averages
# - Basic comparisons
#
# The engine returns structured information so that brain.py
# can decide how much of the reasoning to show the user.
# ============================================================


# ------------------------------------------------------------
# SAFE CALCULATOR
# ------------------------------------------------------------

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    try:
        tree = ast.parse(expression, mode="eval")
        return _evaluate(tree.body)

    except Exception:
        return None


def _evaluate(node):

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value

        raise ValueError("Invalid number")

    if isinstance(node, ast.UnaryOp):
        operation = OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Invalid operator")

        return operation(_evaluate(node.operand))

    if isinstance(node, ast.BinOp):
        operation = OPERATORS.get(type(node.op))

        if operation is None:
            raise ValueError("Invalid operator")

        left = _evaluate(node.left)
        right = _evaluate(node.right)

        if isinstance(node.op, ast.Div) and right == 0:
            raise ZeroDivisionError

        return operation(left, right)

    raise ValueError("Unsupported expression")


# ------------------------------------------------------------
# NORMALIZATION
# ------------------------------------------------------------

def normalize(text):

    text = text.lower().strip()

    replacements = {
        "×": "*",
        "÷": "/",
        "−": "-",
        "–": "-",
        "—": "-",
        "^": "**",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


# ------------------------------------------------------------
# DETECTION
# ------------------------------------------------------------

def looks_like_math(text):

    text = normalize(text)

    math_words = [
        "calculate",
        "solve",
        "equation",
        "percentage",
        "percent",
        "ratio",
        "fraction",
        "average",
        "mean",
        "probability",
        "area",
        "perimeter",
        "volume",
        "speed",
        "distance",
        "time",
        "how much",
        "how many",
        "what is",
        "what's",
        "equals",
        "equal to",
        "plus",
        "minus",
        "times",
        "divided by",
    ]

    has_math_symbol = bool(
        re.search(r"\d+\s*[\+\-\*/%]\s*\d+", text)
    )

    has_math_word = any(
        word in text for word in math_words
    )

    return has_math_symbol or has_math_word


# ------------------------------------------------------------
# RESULT BUILDER
# ------------------------------------------------------------

def build_result(
    problem_type,
    answer,
    steps,
    method
):

    return {
        "type": problem_type,
        "answer": answer,
        "method": method,
        "steps": steps,
        "verified": verify(answer),
    }


# ------------------------------------------------------------
# ARITHMETIC
# ------------------------------------------------------------

def solve_arithmetic(text):

    expression_pattern = (
        r"(?<!\w)"
        r"(\d+(?:\.\d+)?"
        r"\s*(?:\+|-|\*|/|%|\*\*)"
        r"\s*\d+(?:\.\d+)?)"
        r"(?!\w)"
    )

    match = re.search(expression_pattern, text)

    if not match:
        return None

    expression = match.group(1)

    result = safe_calculate(expression)

    if result is None:
        return None

    return build_result(
        problem_type="arithmetic",
        answer=result,
        method="direct arithmetic",
        steps=[
            f"Identify the expression: {expression}",
            f"Calculate {expression}",
            f"Result = {result}",
        ],
    )


# ------------------------------------------------------------
# PERCENTAGES
# ------------------------------------------------------------

def solve_percentage(text):

    pattern = (
        r"(\d+(?:\.\d+)?)"
        r"\s*(?:%|percent)"
        r"\s*(?:of)"
        r"\s*(\d+(?:\.\d+)?)"
    )

    match = re.search(pattern, text)

    if match:

        percentage = float(match.group(1))
        number = float(match.group(2))

        decimal = percentage / 100
        result = decimal * number

        return build_result(
            problem_type="percentage",
            answer=result,
            method="percentage of a number",
            steps=[
                f"Identify {percentage}% of {number}",
                f"Convert {percentage}% to {decimal}",
                f"Calculate {decimal} × {number}",
                f"Result = {result}",
            ],
        )

    return None


# ------------------------------------------------------------
# FRACTIONS
# ------------------------------------------------------------

def solve_fraction(text):

    pattern = (
        r"(\d+)\s*/\s*(\d+)"
        r"\s*(?:of)"
        r"\s*(\d+(?:\.\d+)?)"
    )

    match = re.search(pattern, text)

    if not match:
        return None

    numerator = float(match.group(1))
    denominator = float(match.group(2))
    number = float(match.group(3))

    if denominator == 0:
        return None

    fraction = numerator / denominator
    result = fraction * number

    return build_result(
        problem_type="fraction",
        answer=result,
        method="fraction of a number",
        steps=[
            f"Identify the fraction {numerator}/{denominator}",
            f"Convert it to {fraction}",
            f"Calculate {fraction} × {number}",
            f"Result = {result}",
        ],
    )


# ------------------------------------------------------------
# AVERAGE
# ------------------------------------------------------------

def solve_average(text):

    match = re.search(
        r"(?:average|mean)\s+(?:of)?\s*"
        r"((?:\d+(?:\.\d+)?\s*,?\s*)+)",
        text,
    )

    if not match:
        return None

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        match.group(1)
    )

    if not numbers:
        return None

    values = [float(number) for number in numbers]

    total = sum(values)
    count = len(values)
    result = total / count

    return build_result(
        problem_type="average",
        answer=result,
        method="arithmetic mean",
        steps=[
            f"Identify the values: {values}",
            f"Add them: {total}",
            f"Count the values: {count}",
            f"Divide {total} by {count}",
            f"Result = {result}",
        ],
    )


# ------------------------------------------------------------
# COMPARISON
# ------------------------------------------------------------

def solve_comparison(text):

    match = re.search(
        r"(?:is|which is)\s+"
        r"([0-9]+(?:\.[0-9]+)?)"
        r"\s+"
        r"(?:bigger than|greater than|larger than|less than|smaller than)"
        r"\s+"
        r"([0-9]+(?:\.[0-9]+)?)",
        text,
    )

    if not match:
        return None

    first = float(match.group(1))
    second = float(match.group(2))

    if "less" in text or "smaller" in text:
        answer = first < second
    else:
        answer = first > second

    return build_result(
        problem_type="comparison",
        answer=answer,
        method="numerical comparison",
        steps=[
            f"Compare {first} and {second}",
            f"Result = {answer}",
        ],
    )


# ------------------------------------------------------------
# VERIFICATION
# ------------------------------------------------------------

def verify(answer):

    if answer is None:
        return False

    if isinstance(answer, bool):
        return True

    if isinstance(answer, (int, float)):
        return math.isfinite(answer)

    return False


# ------------------------------------------------------------
# MAIN SOLVER
# ------------------------------------------------------------

def solve(question):

    text = normalize(question)

    if not looks_like_math(text):
        return None

    solvers = [
        solve_percentage,
        solve_fraction,
        solve_average,
        solve_comparison,
        solve_arithmetic,
    ]

    for solver in solvers:

        result = solver(text)

        if result is None:
            continue

        if result["verified"]:
            return result

    return None
